import os, json, ssl, gzip, shutil, threading
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config_manager import ConfigManager
import time

class NotificationManager:
    SMTP_CONFIGS = {
        "gmail":  {"server": "smtp.gmail.com",       "port": 465, "ssl": True},
        "yahoo":  {"server": "smtp.mail.yahoo.com",  "port": 465, "ssl": True},
        "icloud": {"server": "smtp.mail.me.com",     "port": 587, "ssl": False},  # STARTTLS
        "apple":  {"server": "smtp.mail.me.com",     "port": 587, "ssl": False},  # alias for icloud
    }

    # minutes: 5, 30, 60, 360 (6h), 720 (12h), 1440 (24h)
    BACKOFF_SCHEDULE = [5, 30, 60, 360, 720, 1440]

    configManager = ConfigManager('config.ini')
    LOGFILE = configManager.get_config('logfile')
    MAX_LOG_SIZE = configManager.get_int_config('max_log_size')
    MAX_ARCHIVE_SIZE = configManager.get_int_config('max_archive_size')

    def __init__(
        self,
        logger,
        provider: str,
        email: str,
        password: str,
        recipients,
        queue_file: str = "email_queue.json",
        retry_days: int = 7,
        poll_interval: int = 300,        # seconds between background checks
        auto_start: bool = True,
    ):
        provider = provider.lower()
        if provider not in self.SMTP_CONFIGS:
            raise ValueError(f"Unsupported provider '{provider}'. Use gmail|yahoo|icloud|apple")
        self.logger = logger
        self.provider = provider
        self.email = email           # also used as SMTP username
        self.password = password
        self.recipients = recipients if isinstance(recipients, list) else [recipients]
        self.queue_file = queue_file
        self.retry_days = retry_days
        self.poll_interval = poll_interval

        self._stop_evt = threading.Event()
        self._thread = None

        # load persisted queue
        self.queue = []
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, "r") as f:
                    self.queue = json.load(f)
            except Exception:
                self.queue = []  # start clean if corrupted

        if auto_start:
            self.start_worker()

    # ---------- Public high-level helpers ----------

    def send_status(self, body: str, subject: str = "System Status", recipients=None):
        """Queue a plain-text status email."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"{timestamp}: {body}")
        self.logger.log(timestamp, 'INFO', 'SYSTEM', 'NOTIFICATION', f"Status update sent...")
        self._queue_message(subject, body, recipients, attachments=None)

    def send_log(self, log_path: str, subject: str = "System Log", recipients=None):
        """Compress the given log file and queue an email with it attached.
           The compressed file is deleted automatically after a successful send.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if not os.path.exists(log_path):
            print(f"Log not found: {log_path}")
            self.logger.log(timestamp, 'WARN', 'SYSTEM', 'NOTIFICATION', f"Log not found: {log_path}")
            return
        gz_path = self._compress_log(log_path)
        self.logger.log(timestamp, 'INFO', 'SYSTEM', 'NOTIFICATION', f"Log file sent: {log_path}")
        # mark for deletion after success
        self._queue_message(subject, "Attached is the latest log.", recipients, attachments=[{"path": gz_path, "delete_after": True}])

    def start_worker(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop_worker(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=self.poll_interval + 2)

    # ---------- Core queueing / processing ----------

    def _queue_message(self, subject, body, recipients=None, attachments=None):
        msg = {
            "subject": subject,
            "body": body,
            "recipients": (recipients if recipients else self.recipients),
            "attachments": attachments or [],  # list of {"path": str, "delete_after": bool}
            "retry_count": 0,
            "next_attempt": datetime.utcnow().timestamp(),
            "created": datetime.utcnow().timestamp(),
        }
        self.queue.append(msg)
        self._save_queue()

    def _worker_loop(self):
        while not self._stop_evt.is_set():
            try:
                self.process_queue()
            except Exception as e:
                print(f"Notifier worker error: {e}")
            # wait, but wake early on stop
            self._stop_evt.wait(self.poll_interval)

    def process_queue(self):
        """Attempt to deliver due messages; reschedule with backoff on failure; drop expired."""
        now = datetime.utcnow().timestamp()
        cutoff = now - (self.retry_days * 86400)

        pending = []
        for msg in self.queue:
            # drop if too old
            if msg.get("created", now) < cutoff:
                print(f"Dropping expired message: {msg.get('subject')}")
                # cleanup any attachment files that were created for this message
                self._cleanup_attachments(msg, success=True)
                continue

            # not yet due
            if msg.get("next_attempt", now) > now:
                pending.append(msg)
                continue

            # try send
            if self._deliver(msg):
                print(f"Delivered: {msg.get('subject')}")
                self._cleanup_attachments(msg, success=True)
            else:
                # schedule retry
                msg["retry_count"] = int(msg.get("retry_count", 0)) + 1
                idx = min(msg["retry_count"], len(self.BACKOFF_SCHEDULE)) - 1
                wait_min = self.BACKOFF_SCHEDULE[idx]
                msg["next_attempt"] = (datetime.utcnow() + timedelta(minutes=wait_min)).timestamp()
                pending.append(msg)
                print(f"⏳ Rescheduled '{msg.get('subject')}' in {wait_min} min")

        self.queue = pending
        self._save_queue()

    def _deliver(self, msg):
        cfg = self.SMTP_CONFIGS[self.provider]
        mime = MIMEMultipart()
        mime["From"] = self.email
        mime["To"] = ", ".join(msg["recipients"])
        mime["Subject"] = msg["subject"]
        mime.attach(MIMEText(msg["body"], "plain"))

        # attachments
        for a in msg.get("attachments", []):
            path = a["path"]
            try:
                with open(path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(path))
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
                mime.attach(part)
            except Exception as e:
                print(f"Could not attach {path}: {e}")

        try:
            if cfg["ssl"]:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(cfg["server"], cfg["port"], context=context) as server:
                    server.login(self.email, self.password)
                    server.sendmail(self.email, msg["recipients"], mime.as_string())
            else:
                with smtplib.SMTP(cfg["server"], cfg["port"]) as server:
                    server.starttls()
                    server.login(self.email, self.password)
                    server.sendmail(self.email, msg["recipients"], mime.as_string())
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False

    # ---------- Utilities ----------

    def _compress_log(self, log_file, out_file=None):
        out_file = out_file or (log_file + ".gz")
        with open(log_file, "rb") as f_in, gzip.open(out_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return out_file

    def _cleanup_attachments(self, msg, success: bool):
        """Delete attachments flagged for deletion after successful send."""
        if not success:
            return
        for a in msg.get("attachments", []):
            if a.get("delete_after") and os.path.exists(a["path"]):
                try:
                    os.remove(a["path"])
                except Exception:
                    pass

    def _save_queue(self):
        try:
            with open(self.queue_file, "w") as f:
                json.dump(self.queue, f)
        except Exception as e:
            print(f"Could not save queue: {e}")
