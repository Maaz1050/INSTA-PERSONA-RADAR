import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Mailer:
    def __init__(self):
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_APP_PASS")
        self.recipient = os.getenv("RECIPIENT_EMAIL", self.smtp_user)

    def build_html(self, new_users: list, reports: list) -> str:
        """Constructs a responsive, dark-themed HTML email."""
        cards_html = ""
        for r in reports:
            # Safely get data from the nested report structure
            profile = r.get("profile", {})
            math = r.get("math", {})
            vision = r.get("vision", {})
            text = r.get("text", {})
            synth = r.get("synth", {})

            cards_html += f"""
            <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;padding:16px;margin-bottom:16px;">
                <h3 style="margin:0 0 8px 0;color:#f4f4f5;">@{profile.get('username')} 
                    <span style="font-size:12px;color:#a1a1aa;font-weight:normal;">
                        ({profile.get('followers', 0)} followers | ER: {math.get('engagement_rate_pct', 0)}%)
                    </span>
                </h3>
                <p style="margin:6px 0;color:#d4d4d8;"><b>Inferred Hobbies:</b> <span style="color:#4ade80;">{', '.join(synth.get('inferred_hobbies', []))}</span></p>
                <p style="margin:6px 0;color:#d4d4d8;"><b>Visual Aesthetic:</b> {synth.get('aesthetic_vibe', 'Unknown')}</p>
                <p style="margin:6px 0;color:#d4d4d8;"><b>Chronotype / Active Window:</b> {math.get('chronotype', 'Unknown')}</p>
                <p style="margin:6px 0;color:#d4d4d8;"><b>Top Hashtags:</b> <code>{' | '.join(text.get('top_hashtags', []))}</code></p>
                <div style="margin-top:10px;padding:10px;background:#27272a;border-radius:6px;">
                    <p style="margin:0;color:#e4e4e7;font-size:14px;font-style:italic;">"{synth.get('executive_summary', 'No summary available.')}"</p>
                </div>
            </div>
            """

        return f"""
        <html>
        <body style="background:#09090b;color:#e4e4e7;font-family:sans-serif;padding:20px;">
            <h2 style="color:#ffffff;border-bottom:1px solid #27272a;padding-bottom:10px;">
                Instagram Persona Intelligence Digest
            </h2>
            <p style="color:#a1a1aa;font-size:14px;">
                Newly Analyzed Targets: <b>{len(new_users)}</b>
            </p>
            {cards_html}
        </body>
        </html>
        """

    def send_report(self, new_users: list, reports: list):
        """Sends the HTML report via Gmail SMTP."""
        if not self.smtp_user or not self.smtp_pass:
            print("[!] SMTP credentials missing. Skipping email dispatch.")
            return

        html_body = self.build_html(new_users, reports)
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Persona Radar] {len(new_users)} New Intelligence Profiles Ready"
        msg["From"] = f"Insta Persona Radar <{self.smtp_user}>"
        msg["To"] = self.recipient

        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_user, self.recipient, msg.as_string())
            print(f"[+] Email successfully dispatched to {self.recipient}")
        except Exception as e:
            print(f"[!] Failed to send email: {e}")
