import httpx
from src.models import Users
from config import settings

BREVO_API_KEY = settings.BREVO_API_KEY
FROM_EMAIL = settings.FROM_EMAIL or "proofaiapp@gmail.com"
FRONTEND_URL = settings.FRONTEND_URL or "http://localhost:3000"

def _verification_html(token: str, user_name: str) -> str:
    verify_url = f"{FRONTEND_URL}/auth/verify-email?token={token}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Proof</h1>
        </div>
        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb;">
            <h2 style="color: #111827; margin-top: 0;">Verify your email address</h2>
            <p>Hi {user_name},</p>
            <p>Thanks for signing up! Please verify your email address to activate your account.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p style="font-size: 14px; color: #6b7280;">Or copy and paste this link into your browser:</p>
            <p style="font-size: 14px; color: #6b7280; word-break: break-all;">{verify_url}</p>
            <p style="font-size: 12px; color: #9ca3af;">This link will expire in 24 hours.</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="font-size: 12px; color: #9ca3af;">If you didn't create an account, you can safely ignore this email.</p>
        </div>
    </body>
    </html>
    """


def _reset_password_html(token: str, user_name: str) -> str:
    reset_url = f"{FRONTEND_URL}/auth/reset-password?token={token}"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Proof</h1>
        </div>
        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb;">
            <h2 style="color: #111827; margin-top: 0;">Reset your password</h2>
            <p>Hi {user_name},</p>
            <p>You requested a password reset for your Proof account. Click the button below to choose a new password.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background: #3b82f6; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="font-size: 14px; color: #6b7280;">Or copy and paste this link into your browser:</p>
            <p style="font-size: 14px; color: #6b7280; word-break: break-all;">{reset_url}</p>
            <p style="font-size: 12px; color: #9ca3af;">This link will expire in 1 hour.</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="font-size: 12px; color: #9ca3af;">If you didn't request this, you can safely ignore this email. Your password won't change.</p>
        </div>
    </body>
    </html>
    """


def _send_email(
    to_email: str,
    subject: str,
    html_body: str,
) -> dict:
    """Send email via Brevo API."""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY or "",
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": "Proof", "email": FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    
    response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
    if response.status_code >= 400:
        raise Exception(f"Brevo API error: {response.status_code} - {response.text}")
    return response.json()


async def send_email_verification(user: Users, token: str) -> dict:
    """Send email verification link."""
    html = _verification_html(token=token, user_name=user.name or "there")
    return _send_email(
        to_email=user.email,
        subject="Verify your email address - Proof",
        html_body=html,
    )


async def send_password_reset_email(user: Users, token: str) -> dict:
    """Send password reset link."""
    html = _reset_password_html(token=token, user_name=user.name or "there")
    return _send_email(
        to_email=user.email,
        subject="Reset your password - Proof",
        html_body=html,
    )
