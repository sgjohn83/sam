from dataclasses import dataclass


@dataclass
class NotificationTemplate:
    template_name: str           # maps to templates/emails/{name}.html
    subject_template: str        # Python format string with {variables}
    push_title: str | None       # None = no push for this type
    push_body_template: str | None
    push_channel: str            # Expo notification channel


NOTIFICATION_TYPES = {
    'document_reupload_request': NotificationTemplate(
        template_name='document_reupload_request',
        subject_template='Action Required: Please re-upload your {document_type}',
        push_title='Document needs re-upload',
        push_body_template='{document_type} was rejected: {reason_preview}',
        push_channel='document_alerts',
    ),
    'fee_payment_request': NotificationTemplate(
        template_name='fee_payment_request',
        subject_template='Fee Payment Due — Application {application_number}',
        push_title='Fee payment required',
        push_body_template='₹{fee_amount} due by {deadline}. Tap to view details.',
        push_channel='admission_alerts',
    ),
    'fee_payment_reminder': NotificationTemplate(
        template_name='fee_payment_reminder',
        subject_template='Reminder: Fee Payment Due {deadline} — {application_number}',
        push_title='Fee payment reminder',
        push_body_template='₹{fee_amount} due in {days_remaining} days.',
        push_channel='admission_alerts',
    ),
    'admission_confirmed': NotificationTemplate(
        template_name='admission_confirmed',
        subject_template='Admission Confirmed — Welcome!',
        push_title='Admission confirmed! 🎓',
        push_body_template='Welcome to {branch_name}. Tap for next steps.',
        push_channel='admission_alerts',
    ),
    'fee_payment_overdue': NotificationTemplate(
        template_name='fee_payment_overdue',
        subject_template='URGENT: Fee Payment Overdue — {application_number}',
        push_title='Fee payment overdue! ⚠️',
        push_body_template='₹{fee_amount} was due {days_overdue} days ago.',
        push_channel='admission_alerts',
    ),
    'agent_student_invite': NotificationTemplate(
        template_name='agent_student_invite',
        subject_template='You have been registered for admission by {agent_name}',
        push_title=None,  # no push — student hasn't installed app yet
        push_body_template=None,
        push_channel='default',
    ),
    'commission_approved': NotificationTemplate(
        template_name='commission_approved',
        subject_template='Commission Approved — ₹{commission_amount} for {student_name}',
        push_title='Commission approved',
        push_body_template='₹{commission_amount} approved for {student_name}',
        push_channel='commission_alerts',
    ),
    'commission_paid': NotificationTemplate(
        template_name='commission_paid',
        subject_template='Commission Paid — ₹{total_amount} transferred',
        push_title='Commission paid! 💰',
        push_body_template='₹{total_amount} transferred. Ref: {payment_reference}',
        push_channel='commission_alerts',
    ),
    'commission_rejected': NotificationTemplate(
        template_name='commission_rejected',
        subject_template='Commission Update — {student_name}',
        push_title='Commission update',
        push_body_template='Commission for {student_name} was not approved.',
        push_channel='commission_alerts',
    ),
}