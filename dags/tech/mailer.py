import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable, Union, Optional, Sequence


class YandexMailer:
    """
    Класс для отправки писем через SMTP Яндекса.

    Пример:
        mailer = YandexMailer(
            login="you@yandex.ru",
            password=os.getenv("YANDEX_APP_PASSWORD"),  # пароль приложения
            use_ssl=True
        )

        mailer.send(
            subject="Тест",
            to=["user@example.com"],
            text="Привет!",
            html="<h1>Привет!</h1><p>Это <b>HTML</b> версия письма.</p>",
            attachments=["/path/to/file.pdf"]
        )
    """

    def __init__(
        self,
        login: str,
        password: str,
        host: str = "smtp.yandex.ru",
        port_ssl: int = 465,
        port_tls: int = 587,
        use_ssl: bool = True,
        timeout: Optional[int] = 30,
    ):
        self.login = login
        self.password = password
        self.host = host
        self.port = port_ssl if use_ssl else port_tls
        self.use_ssl = use_ssl
        self.timeout = timeout

    def _connect(self) -> smtplib.SMTP:
        if self.use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(
                self.host, self.port, timeout=self.timeout, context=context
            )
        else:
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            server.starttls(context=ssl.create_default_context())
        server.login(self.login, self.password)
        return server

    @staticmethod
    def _normalize_recipients(addresses: Union[str, Iterable[str]]) -> Sequence[str]:
        if isinstance(addresses, str):
            return [addresses]
        return list(addresses)

    @staticmethod
    def _attach_files(msg: EmailMessage, attachments: Iterable[str]) -> None:
        import mimetypes
        from pathlib import Path

        for path_str in attachments:
            path = Path(path_str)
            ctype, encoding = mimetypes.guess_type(path.name)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)

            with path.open("rb") as f:
                msg.add_attachment(
                    f.read(), maintype=maintype, subtype=subtype, filename=path.name
                )

    def build_message(
        self,
        subject: str,
        to: Union[str, Iterable[str]],
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, Iterable[str]]] = None,
        bcc: Optional[Union[str, Iterable[str]]] = None,
        attachments: Optional[Iterable[str]] = None,
        reply_to: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{self.login}>" if from_name else self.login

        to_list = self._normalize_recipients(to)
        msg["To"] = ", ".join(to_list)

        if cc:
            cc_list = self._normalize_recipients(cc)
            msg["Cc"] = ", ".join(cc_list)
        else:
            cc_list = []

        if reply_to:
            msg["Reply-To"] = reply_to

        # Текст / HTML
        if html and text:
            msg.set_content(text)
            msg.add_alternative(html, subtype="html")
        elif html:
            msg.set_content("Ваш почтовый клиент не поддерживает HTML.")
            msg.add_alternative(html, subtype="html")
        elif text:
            msg.set_content(text)
        else:
            raise ValueError("Нужно передать хотя бы text или html.")

        # Вложения
        if attachments:
            self._attach_files(msg, attachments)

        # Возвращаем сообщение и полный список получателей (для bcc)
        all_recipients = (
            to_list + cc_list + (self._normalize_recipients(bcc) if bcc else [])
        )
        return msg, all_recipients

    def send(
        self,
        subject: str,
        to: Union[str, Iterable[str]],
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, Iterable[str]]] = None,
        bcc: Optional[Union[str, Iterable[str]]] = None,
        attachments: Optional[Iterable[str]] = None,
        reply_to: Optional[str] = None,
        from_name: Optional[str] = None,
    ):
        msg, recipients = self.build_message(
            subject=subject,
            to=to,
            text=text,
            html=html,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            reply_to=reply_to,
            from_name=from_name,
        )

        with self._connect() as server:
            server.send_message(msg, from_addr=self.login, to_addrs=recipients)
