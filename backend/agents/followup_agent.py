import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import re

from ..config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, 
    EMAIL_FROM, BASE_DIR
)

class FollowUpAgent:
    """Follow-up Agent for sending emails and SMS notifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.email_username = EMAIL_USERNAME
        self.email_password = EMAIL_PASSWORD
        self.email_from = EMAIL_FROM
        
        # Email templates
        self.email_templates = self._setup_email_templates()
        
        # Track sent emails
        self.sent_emails_log = BASE_DIR / 'logs' / 'sent_emails.json'
        self.sent_emails_log.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_email_templates(self):
        """Setup email templates for different inquiry types"""
        return {
            'general': {
                'subject': 'Thank you for your inquiry - {university_name}',
                'template': '''
Dear {name},

Thank you for contacting our admissions office! We're excited about your interest in {university_name}.

Based on our conversation, here's a summary of what we discussed:

{conversation_summary}

Next Steps:
{next_steps}

Important Dates to Remember:
• Application Deadline: March 1st (Fall), October 1st (Spring)
• Financial Aid Priority Deadline: March 1st
• Campus Visit Registration: Available year-round

Resources for You:
• Admissions Website: www.university.edu/admissions
• Virtual Campus Tour: www.university.edu/tour
• Financial Aid Calculator: www.university.edu/calculator

If you have any additional questions, please don't hesitate to contact us:
• Email: admissions@university.edu
• Phone: (555) 123-4567
• Office Hours: Monday-Friday, 8:00 AM - 5:00 PM

We look forward to hearing from you soon!

Best regards,
{university_name} Admissions Team

---
This email was sent as a follow-up to your recent inquiry. If you did not request this information, please contact us at admissions@university.edu.
                '''
            },
            'admission_requirements': {
                'subject': 'Admission Requirements Information - {university_name}',
                'template': '''
Dear {name},

Thank you for your inquiry about admission requirements for {university_name}.

Here's a complete checklist of what you'll need for your application:

REQUIRED DOCUMENTS:
□ Completed online application
□ Official high school transcripts
□ SAT (1200+) or ACT (26+) scores
□ Two letters of recommendation
□ Personal statement/essay
□ Application fee ($50)

ADDITIONAL REQUIREMENTS (Program-specific):
□ Portfolio (Art, Design programs)
□ Audition (Music, Theater programs)
□ Prerequisites (Engineering, Pre-med programs)

DEADLINES:
• Fall Semester: March 1st (Regular), November 15th (Early Decision)
• Spring Semester: October 1st
• Summer Semester: March 1st

{conversation_summary}

Ready to Apply?
Start your application at: www.university.edu/apply

Questions? Contact us:
• Email: admissions@university.edu
• Phone: (555) 123-4567

Best of luck with your application!

{university_name} Admissions Team
                '''
            },
            'financial_aid': {
                'subject': 'Financial Aid Information - {university_name}',
                'template': '''
Dear {name},

Thank you for your inquiry about financial aid opportunities at {university_name}.

FINANCIAL AID OPTIONS:
• Federal Grants (Pell Grant, SEOG)
• State Grants and Scholarships
• University Merit Scholarships
• Need-based Aid
• Work-Study Programs
• Student Loans

IMPORTANT DATES:
• FAFSA Priority Deadline: March 1st
• Scholarship Application Deadline: February 1st
• Verification Documents Due: May 1st

{conversation_summary}

TO APPLY FOR FINANCIAL AID:
1. Complete FAFSA at studentaid.gov (School Code: 123456)
2. Submit required verification documents
3. Apply for university scholarships
4. Review your financial aid package

ESTIMATED COSTS (2024-2025):
• In-state Tuition: $12,000/year
• Out-of-state Tuition: $28,000/year
• Room & Board: $14,000/year
• Books & Supplies: $1,500/year

Over 80% of our students receive some form of financial aid!

Questions about financial aid?
• Email: finaid@university.edu
• Phone: (555) 123-4568
• Financial Aid Calculator: www.university.edu/calculator

Best regards,
{university_name} Financial Aid Office
                '''
            },
            'programs': {
                'subject': 'Academic Programs Information - {university_name}',
                'template': '''
Dear {name},

Thank you for your interest in our academic programs at {university_name}.

{conversation_summary}

POPULAR UNDERGRADUATE PROGRAMS:
• Business Administration
• Computer Science
• Engineering
• Pre-Health Programs
• Psychology
• Education
• Arts & Sciences

GRADUATE PROGRAMS:
• MBA (Full-time, Part-time, Executive)
• Master's Programs (30+ fields)
• Doctoral Programs (PhD, Professional)

PROGRAM HIGHLIGHTS:
• Small class sizes (15:1 student-faculty ratio)
• Hands-on learning opportunities
• Industry partnerships and internships
• Research opportunities for undergraduates
• Study abroad programs

NEXT STEPS:
• Explore programs: www.university.edu/academics
• Schedule a program-specific meeting
• Attend an information session
• Connect with current students

Contact Academic Advisors:
• Business: business@university.edu
• Engineering: engineering@university.edu
• Arts & Sciences: artsci@university.edu
• General Inquiries: admissions@university.edu

We're here to help you find the perfect program!

{university_name} Admissions Team
                '''
            }
        }
    
    def send_followup_email(self, email: str, name: str, inquiry_type: str, conversation_history: List[Dict]) -> bool:
        """Send follow-up email based on inquiry type"""
        try:
            if not self._validate_email_config():
                self.logger.error("Email configuration not properly set")
                return False
            
            if not self._validate_email_address(email):
                self.logger.error(f"Invalid email address: {email}")
                return False
            
            # Generate email content
            email_content = self._generate_email_content(
                email, name, inquiry_type, conversation_history
            )
            
            if not email_content:
                self.logger.error("Failed to generate email content")
                return False
            
            # Send email
            success = self._send_email(
                to_email=email,
                subject=email_content['subject'],
                body=email_content['body'],
                is_html=email_content.get('is_html', False)
            )
            
            if success:
                # Log sent email
                self._log_sent_email(email, name, inquiry_type, email_content['subject'])
                self.logger.info(f"Follow-up email sent successfully to {email}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending follow-up email: {e}")
            return False
    
    def _generate_email_content(self, email: str, name: str, inquiry_type: str, conversation_history: List[Dict]) -> Dict:
        """Generate email content based on inquiry type and conversation"""
        try:
            # Get appropriate template
            template_key = inquiry_type if inquiry_type in self.email_templates else 'general'
            template_data = self.email_templates[template_key]
            
            # Generate conversation summary
            conversation_summary = self._generate_conversation_summary(conversation_history)
            
            # Generate next steps
            next_steps = self._generate_next_steps(inquiry_type, conversation_history)
            
            # Template variables
            template_vars = {
                'name': name,
                'university_name': 'Your University Name',  # This should be configurable
                'conversation_summary': conversation_summary,
                'next_steps': next_steps,
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'inquiry_type': inquiry_type.replace('_', ' ').title()
            }
            
            # Format subject and body
            subject = template_data['subject'].format(**template_vars)
            body = template_data['template'].format(**template_vars)
            
            return {
                'subject': subject,
                'body': body,
                'is_html': False
            }
            
        except Exception as e:
            self.logger.error(f"Error generating email content: {e}")
            return {}
    
    def _generate_conversation_summary(self, conversation_history: List[Dict]) -> str:
        """Generate a summary of the conversation"""
        try:
            if not conversation_history:
                return "We had a brief conversation about your interest in our university."
            
            # Extract key topics discussed
            topics = set()
            questions_asked = []
            
            for interaction in conversation_history[-5:]:  # Last 5 interactions
                intent = interaction.get('intent', '')
                user_input = interaction.get('user_input', '')
                
                if intent and intent != 'unknown':
                    topics.add(intent.replace('_', ' ').title())
                
                if user_input and len(user_input) > 10:
                    questions_asked.append(user_input[:100] + ('...' if len(user_input) > 100 else ''))
            
            summary_parts = []
            
            if topics:
                topics_list = ', '.join(sorted(topics))
                summary_parts.append(f"During our conversation, we discussed: {topics_list}.")
            
            if questions_asked:
                summary_parts.append("Some of your specific questions included:")
                for i, question in enumerate(questions_asked[:3], 1):
                    summary_parts.append(f"{i}. {question}")
            
            if not summary_parts:
                return "Thank you for your interest in our university programs and admissions process."
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating conversation summary: {e}")
            return "Thank you for your inquiry about our university."
    
    def _generate_next_steps(self, inquiry_type: str, conversation_history: List[Dict]) -> str:
        """Generate personalized next steps based on inquiry type"""
        next_steps_map = {
            'admission_requirements': [
                "1. Review the complete requirements checklist above",
                "2. Start gathering your required documents",
                "3. Register for SAT/ACT if needed",
                "4. Begin your online application",
                "5. Schedule a campus visit or virtual tour"
            ],
            'application_deadline': [
                "1. Mark important deadlines in your calendar",
                "2. Start your application early to avoid rush",
                "3. Prepare required documents in advance",
                "4. Submit FAFSA by the priority deadline",
                "5. Follow up on application status regularly"
            ],
            'financial_aid': [
                "1. Complete FAFSA at studentaid.gov",
                "2. Apply for university scholarships",
                "3. Research external scholarship opportunities",
                "4. Submit required verification documents",
                "5. Schedule a financial aid counseling session"
            ],
            'programs_offered': [
                "1. Explore detailed program information on our website",
                "2. Schedule a meeting with an academic advisor",
                "3. Attend a program-specific information session",
                "4. Connect with current students in your field of interest",
                "5. Consider scheduling a campus visit"
            ],
            'general': [
                "1. Explore our website for detailed information",
                "2. Schedule a campus visit or virtual tour",
                "3. Attend an upcoming information session",
                "4. Connect with our admissions counselors",
                "5. Start your application when ready"
            ]
        }
        
        steps = next_steps_map.get(inquiry_type, next_steps_map['general'])
        return '\n'.join(steps)
    
    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def _validate_email_config(self) -> bool:
        """Validate email configuration"""
        required_configs = [
            self.smtp_server, self.smtp_port, 
            self.email_username, self.email_password, self.email_from
        ]
        return all(config for config in required_configs)
    
    def _validate_email_address(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _log_sent_email(self, email: str, name: str, inquiry_type: str, subject: str):
        """Log sent email for tracking"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'email': email,
                'name': name,
                'inquiry_type': inquiry_type,
                'subject': subject
            }
            
            # Load existing logs
            logs = []
            if self.sent_emails_log.exists():
                try:
                    with open(self.sent_emails_log, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Save logs
            with open(self.sent_emails_log, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error logging sent email: {e}")
    
    def send_reminder_email(self, email: str, name: str, reminder_type: str, days_until_deadline: int) -> bool:
        """Send reminder email for important deadlines"""
        try:
            reminder_templates = {
                'application_deadline': {
                    'subject': f'Reminder: Application Deadline in {days_until_deadline} days',
                    'body': f'''
Dear {name},

This is a friendly reminder that the application deadline for {reminder_type} is approaching in {days_until_deadline} days.

Don't forget to:
• Complete your online application
• Submit all required documents
• Pay the application fee

Apply now at: www.university.edu/apply

Questions? Contact us at admissions@university.edu

Best regards,
Admissions Team
                    '''
                },
                'financial_aid': {
                    'subject': f'Reminder: FAFSA Deadline in {days_until_deadline} days',
                    'body': f'''
Dear {name},

The FAFSA priority deadline is approaching in {days_until_deadline} days.

Complete your FAFSA at studentaid.gov (School Code: 123456) to be considered for:
• Federal grants and loans
• State financial aid
• University scholarships

Don't miss out on financial aid opportunities!

Financial Aid Office
                    '''
                }
            }
            
            if reminder_type not in reminder_templates:
                return False
            
            template = reminder_templates[reminder_type]
            
            return self._send_email(
                to_email=email,
                subject=template['subject'],
                body=template['body']
            )
            
        except Exception as e:
            self.logger.error(f"Error sending reminder email: {e}")
            return False
    
    def get_email_stats(self, days: int = 30) -> Dict:
        """Get email statistics for the last N days"""
        try:
            if not self.sent_emails_log.exists():
                return {'total_sent': 0, 'by_type': {}, 'recent_emails': []}
            
            with open(self.sent_emails_log, 'r') as f:
                logs = json.load(f)
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_logs = [
                log for log in logs
                if datetime.fromisoformat(log['timestamp']) > cutoff_date
            ]
            
            # Calculate statistics
            by_type = {}
            for log in recent_logs:
                inquiry_type = log.get('inquiry_type', 'unknown')
                by_type[inquiry_type] = by_type.get(inquiry_type, 0) + 1
            
            return {
                'total_sent': len(recent_logs),
                'by_type': by_type,
                'recent_emails': recent_logs[-10:],  # Last 10 emails
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Error getting email stats: {e}")
            return {'total_sent': 0, 'by_type': {}, 'recent_emails': []}
    
    def cleanup(self):
        """Cleanup resources"""
        # Clean up old log entries (keep last 6 months)
        try:
            if self.sent_emails_log.exists():
                with open(self.sent_emails_log, 'r') as f:
                    logs = json.load(f)
                
                cutoff_date = datetime.now() - timedelta(days=180)
                filtered_logs = [
                    log for log in logs
                    if datetime.fromisoformat(log['timestamp']) > cutoff_date
                ]
                
                if len(filtered_logs) < len(logs):
                    with open(self.sent_emails_log, 'w') as f:
                        json.dump(filtered_logs, f, indent=2)
                    
                    self.logger.info(f"Cleaned up {len(logs) - len(filtered_logs)} old email logs")
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        self.logger.info("Follow-up Agent cleaned up")