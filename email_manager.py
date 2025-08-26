"""
Email sending management for restaurant reservations
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import RESTAURANT_INFO


def get_email_config():
    """Retrieve email configuration from environment variables"""
    # Load email settings from environment variables for security
    # This allows different configurations for development/staging/production
    return {
        'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),          # SMTP server address
        'smtp_port': int(os.environ.get('SMTP_PORT', '587')),                    # SMTP port (587 for TLS)
        'email_user': os.environ.get('EMAIL_USER', ''),                          # Sender email address
        'email_password': os.environ.get('EMAIL_PASSWORD', ''),                  # App password (not regular password)
        'sender_name': os.environ.get('SENDER_NAME', RESTAURANT_INFO['name'])    # Display name for sender
    }


def create_confirmation_email_html(reservation_data, language_code='en'):
    """Create HTML template for reservation confirmation email with multilingual support"""
    # Professional HTML email template with modern styling
    # Uses inline CSS for maximum email client compatibility
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            /* Base styling for email body */
            body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            /* Main container with shadow and rounded corners */
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            /* Header with gradient background and white text */
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            /* Main content area */
            .content {{ padding: 30px; }}
            /* Styled box for reservation details */
            .reservation-details {{ background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            /* Individual detail rows with flex layout */
            .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
            .detail-label {{ font-weight: bold; color: #555; }}
            .detail-value {{ color: #333; }}
            /* Large success emoji */
            .success-icon {{ font-size: 48px; margin: 10px 0; }}
            /* Footer with restaurant info */
            .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
            .contact-info {{ margin: 15px 0; }}
            .contact-info a {{ color: #667eea; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Email header with confirmation message -->
            <div class="header">
                <div class="success-icon">🎉</div>
                <h1>Reservation Confirmed!</h1>
                <p>Thank you for choosing {RESTAURANT_INFO['name']}</p>
            </div>
            
            <!-- Main content with reservation details -->
            <div class="content">
                <h2>📋 Your Reservation Details</h2>
                
                <!-- Reservation information in structured format -->
                <div class="reservation-details">
                    <div class="detail-row">
                        <span class="detail-label">👤 Name:</span>
                        <span class="detail-value">{reservation_data['name']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📞 Phone:</span>
                        <span class="detail-value">{reservation_data['phone']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📧 Email:</span>
                        <span class="detail-value">{reservation_data['email']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">👥 Guests:</span>
                        <span class="detail-value">{reservation_data['guests']} people</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📅 Date:</span>
                        <span class="detail-value">{reservation_data['date']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🕐 Time:</span>
                        <span class="detail-value">{reservation_data['time']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">🪑 Table:</span>
                        <span class="detail-value">Table {reservation_data['table']}</span>
                    </div>
                </div>
                
                <!-- Restaurant location and contact information -->
                <h3>📍 Restaurant Information</h3>
                <div class="contact-info">
                    <strong>Address:</strong> {RESTAURANT_INFO['address'].get(language_code, RESTAURANT_INFO['address']['en'])}<br>
                    <strong>Phone:</strong> <a href="tel:{RESTAURANT_INFO['phone']}">{RESTAURANT_INFO['phone']}</a><br>
                    <strong>Email:</strong> <a href="mailto:{RESTAURANT_INFO['email']}">{RESTAURANT_INFO['email']}</a>
                </div>
                
                <!-- Operating hours information -->
                <h3>⏰ Opening Hours</h3>
                <p>
                    Monday - Saturday: 09:00 AM - 09:00 PM<br>
                    Sunday: 10:00 AM - 08:00 PM
                </p>
                
                <!-- Instructions for modifications -->
                <p><strong>Need to modify or cancel?</strong> Simply reply to this email or call us!</p>
            </div>
            
            <!-- Footer with closing message and restaurant description -->
            <div class="footer">
                <p>We look forward to serving you at {RESTAURANT_INFO['name']}!</p>
                <p>{RESTAURANT_INFO['description']['en']}</p>
                <p><small>This is an automated confirmation email. Please save it for your records.</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template


def send_confirmation_email(reservation_data, language_code='en'):
    """Send reservation confirmation email to customer with multilingual support"""
    try:
        # Get email configuration from environment variables
        email_config = get_email_config()
        
        # Check if email configuration is complete before attempting to send
        if not email_config['email_user'] or not email_config['email_password']:
            print("⚠️ Email configuration missing - email not sent")
            return False
        
        # Create multipart message to support both HTML and plain text
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{email_config['sender_name']} <{email_config['email_user']}>"
        msg['To'] = reservation_data['email']
        # Create multilingual subject
        try:
            from translations import get_text
            subject_text = get_text('reservation_confirmed', language_code, 
                                  name=reservation_data['name'], 
                                  guests=reservation_data['guests'],
                                  date=reservation_data['date'], 
                                  time=reservation_data['time'],
                                  table=reservation_data['table'])
            msg['Subject'] = f"✅ {subject_text.split('!')[0]}" 
        except:
            msg['Subject'] = f"✅ Reservation Confirmed at {RESTAURANT_INFO['name']} - {reservation_data['date']}"
        
        # Create HTML version of the email (rich formatting)
        html_content = create_confirmation_email_html(reservation_data, language_code)
        html_part = MIMEText(html_content, 'html')
        
        # Create plain text version (fallback for email clients that don't support HTML)
        text_content = f"""
        🎉 RESERVATION CONFIRMED! 🎉
        
        Thank you for choosing {RESTAURANT_INFO['name']}!
        
        📋 Your Reservation Details:
        👤 Name: {reservation_data['name']}
        📞 Phone: {reservation_data['phone']}
        📧 Email: {reservation_data['email']}
        👥 Guests: {reservation_data['guests']} people
        📅 Date: {reservation_data['date']}
        🕐 Time: {reservation_data['time']}
        🪑 Table: Table {reservation_data['table']}
        
        📍 Restaurant Information:
        Address: {RESTAURANT_INFO['address'].get(language_code, RESTAURANT_INFO['address']['en'])}
        Phone: {RESTAURANT_INFO['phone']}
        Email: {RESTAURANT_INFO['email']}
        
        ⏰ Opening Hours:
        Monday - Saturday: 09:00 AM - 09:00 PM
        Sunday: 10:00 AM - 08:00 PM
        
        Need to modify or cancel? Simply reply to this email or call us!
        
        We look forward to serving you at {RESTAURANT_INFO['name']}!
        {RESTAURANT_INFO['description']['en']}
        """
        text_part = MIMEText(text_content, 'plain')
        
        # Attach both parts to the message (email clients will choose the best one)
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email using SMTP
        print(f"🔧 DEBUG - Attempting to send email to {reservation_data['email']}")
        
        # Establish secure SMTP connection
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            server.starttls()  # Enable encryption for security
            server.login(email_config['email_user'], email_config['email_password'])
            
            # Send the message
            text = msg.as_string()
            server.sendmail(email_config['email_user'], reservation_data['email'], text)
            
        print(f"✅ Confirmation email sent successfully to {reservation_data['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending confirmation email: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        return False


def send_admin_notification(reservation_data, language_code='en'):
    """Send notification to restaurant about new reservation with multilingual support"""
    try:
        # Get email configuration from environment variables
        email_config = get_email_config()
        
        # Check if email configuration is available
        if not email_config['email_user'] or not email_config['email_password']:
            print("⚠️ Email configuration missing - admin notification not sent")
            return False
        
        # Create simple text message for restaurant staff
        # Admin notifications are kept simple for quick reading
        msg = MIMEText(f"""
        🆕 NEW RESERVATION ALERT!
        
        A new reservation has been made:
        
        👤 Customer: {reservation_data['name']}
        📞 Phone: {reservation_data['phone']}
        📧 Email: {reservation_data['email']}
        👥 Guests: {reservation_data['guests']} people
        📅 Date: {reservation_data['date']}
        🕐 Time: {reservation_data['time']}
        🪑 Table: {reservation_data['table']}
        
        Please prepare for the guest's arrival.
        
        - {RESTAURANT_INFO['name']} Reservation System
        """)
        
        # Set email headers for admin notification
        msg['From'] = f"{email_config['sender_name']} System <{email_config['email_user']}>"
        msg['To'] = RESTAURANT_INFO['email']  # Send to restaurant's email address
        msg['Subject'] = f"🆕 New Reservation: {reservation_data['name']} - {reservation_data['date']} {reservation_data['time']}"
        
        # Send email to restaurant admin
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            server.starttls()  # Enable encryption
            server.login(email_config['email_user'], email_config['email_password'])
            server.sendmail(email_config['email_user'], RESTAURANT_INFO['email'], msg.as_string())
            
        print(f"✅ Admin notification sent to {RESTAURANT_INFO['email']}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending admin notification: {e}")
        return False
