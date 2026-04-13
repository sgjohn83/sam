"""
Minimal tests for notification system.
"""
from django.test import TestCase
from django.template.loader import get_template


class NotificationTemplateTests(TestCase):
    """Test that email templates exist and can be rendered."""
    
    def test_fee_payment_request_template_exists(self):
        """Test fee_payment_request email template."""
        template = get_template('emails/fee_payment_request.html')
        context = {
            'student_name': 'Test Student',
            'application_number': 'ADM-2024-00001',
            'branch_name': 'Computer Science',
            'branch_code': 'CS',
            'quota': 'General',
            'fee_amount': '50000',
            'fee_concession': '5000',
            'fee_final': '45000',
            'deadline': '15 April 2024, 11:59 PM',
            'payment_link': 'studentadmission://fee-payment/test-id',
            'support_email': 'admissions@college.edu',
        }
        rendered = template.render(context)
        self.assertIsInstance(rendered, str)
        self.assertGreater(len(rendered), 0)
        self.assertIn('Test Student', rendered)
        self.assertIn('ADM-2024-00001', rendered)
        self.assertIn('₹45000', rendered)
    
    def test_admission_confirmed_template_exists(self):
        """Test admission_confirmed email template."""
        template = get_template('emails/admission_confirmed.html')
        context = {
            'student_name': 'Test Student',
            'application_number': 'ADM-2024-00001',
            'branch_name': 'Computer Science',
            'branch_code': 'CS',
            'quota': 'General',
            'fee_paid_amount': '45000',
            'admitted_date': '12 April 2024',
            'academic_year': '2024-25',
            'orientation_date': '15 June 2024',
            'orientation_venue': 'Main Campus Auditorium',
            'reporting_date': '10 June 2024',
            'dashboard_link': 'studentadmission://dashboard',
            'support_email': 'admissions@college.edu',
        }
        rendered = template.render(context)
        self.assertIsInstance(rendered, str)
        self.assertGreater(len(rendered), 0)
        self.assertIn('Test Student', rendered)
        self.assertIn('Computer Science', rendered)
        self.assertIn('15 June 2024', rendered)
        self.assertIn('Main Campus Auditorium', rendered)
    
    def test_all_templates_exist(self):
        """All required email templates exist."""
        templates = [
            'emails/fee_payment_request.html',
            'emails/fee_payment_request.txt',
            'emails/fee_payment_reminder.html',
            'emails/fee_payment_reminder.txt',
            'emails/fee_payment_overdue.html',
            'emails/fee_payment_overdue.txt',
            'emails/admission_confirmed.html',
            'emails/admission_confirmed.txt',
        ]
        
        for template_name in templates:
            try:
                template = get_template(template_name)
                # Try to render with minimal context
                context = {'student_name': 'Test'}
                rendered = template.render(context)
                self.assertIsInstance(rendered, str)
                self.assertGreater(len(rendered), 0)
            except Exception as e:
                self.fail(f"Template {template_name} failed to render: {e}")
    
    def test_notification_registry_complete(self):
        """All required notification types are registered."""
        from notifications.registry import NOTIFICATION_TYPES
        
        required_types = [
            'fee_payment_request',
            'fee_payment_reminder',
            'fee_payment_overdue',
            'admission_confirmed',
        ]
        
        for notification_type in required_types:
            self.assertIn(notification_type, NOTIFICATION_TYPES)
            
            config = NOTIFICATION_TYPES[notification_type]
            self.assertIsNotNone(config.template_name)
            self.assertIsNotNone(config.subject_template)