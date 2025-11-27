import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def signup_user(email: str, password: str):
    """Register a new user and trigger a welcome email via Supabase Edge Function."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        # Check if we have user data
        if not response.user:
            return {"success": False, "error": "Signup failed - no user returned"}

        # Prepare the response payload we will return to caller
        result = {
            "success": True,
            "user": response.user,
            "session": response.session if getattr(response, "session", None) else None
        }

        # Attempt to send welcome email (fire-and-report; don't fail signup if email send fails)
        try:
            email_payload = {
                "to": email,
                "subject": "Welcome to StockIn!",
                "body": (
                    f"Hi,\n\n"
                    "Welcome to StockIn — we’re glad to have you on board!\n\n"
                    "If you need help, reply to this email or visit our docs.\n\n"
                    "— The StockIn Team"
                )
                # Optionally add other fields like `template_id`, `data`, etc.
            }

            fn_resp = supabase.functions.invoke(
                "send-welcome",
                invoke_options={"body": email_payload}
            )

            # You can inspect fn_resp for status/details; include it in the returned result.
            result["welcome_email"] = {"success": True, "response": fn_resp}

        except Exception as email_err:
            # Do not fail the signup if email sending fails — just report it so you can retry/log.
            result["welcome_email"] = {"success": False, "error": str(email_err)}

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(email: str, password: str):
    """Login existing user"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Check if we have user and session data
        if not response.user or not response.session:
            return {"success": False, "error": "Login failed - invalid credentials"}
        
        return {
            "success": True, 
            "user": response.user, 
            "session": response.session
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_token(token: str):
    """Verify JWT token and return user"""
    try:
        user = supabase.auth.get_user(token)
        return {"success": True, "user": user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def logout_user(token: str):
    """Logout user"""
    try:
        supabase.auth.sign_out()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_email_notification(user_email: str, subject: str, body: str):
    """
    Send email via Supabase Edge Function
    You'll need to create an edge function for this
    """
    try:
        response = supabase.functions.invoke(
            "send-email",
            invoke_options={
                "body": {
                    "to": user_email,
                    "subject": subject,
                    "body": body
                }
            }
        )
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_from_request_header(auth_header: str):
    """Extract and verify user from Authorization header"""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    result = verify_token(token)
    
    if result["success"]:
        return result["user"]
    return None


def check_auth(handler):
    """
    Helper function to check authentication in request handlers.
    Returns user if authenticated, None otherwise.
    Automatically sends 401 response if unauthorized.
    
    Usage in handler:
        user = check_auth(self)
        if not user:
            return
    """
    auth_header = handler.headers.get('Authorization')
    user = get_user_from_request_header(auth_header)
    
    if not user:
        handler._set_headers(401)
        handler.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
        return None
    
    return user