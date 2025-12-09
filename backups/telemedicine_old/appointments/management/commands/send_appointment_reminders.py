from django.core.management.base import BaseCommand
from django.utils import timezone
from core.utils import get_upcoming_appointments, send_appointment_reminder_email
from core.models_communication import CommunicationNotification

class Command(BaseCommand):
    help = 'Sends reminder emails and notifications for upcoming appointments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='How many days ahead to send reminders for appointments (default: 1)'
        )

    def handle(self, *args, **options):
        days = options['days']
        
        # Get upcoming appointments
        appointments = get_upcoming_appointments(days=days)
        
        self.stdout.write(f"{len(appointments)} upcoming appointments found.")
        
        # Send reminder for each appointment
        for appointment in appointments:
            # Send email
            try:
                send_appointment_reminder_email(appointment)
                self.stdout.write(self.style.SUCCESS(
                    f"Email sent: {appointment.patient.email} - {appointment.date}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Email could not be sent: {appointment.patient.email} - Error: {str(e)}"
                ))
            
            # Create notification
            try:
                CommunicationNotification.objects.create(
                    user=appointment.patient,
                    title=f"Appointment Reminder: {appointment.date.strftime('%d.%m.%Y')}",
                    message=f"You have an appointment tomorrow at {appointment.time.strftime('%H:%M')} with Dr. {appointment.doctor.get_full_name()}.",
                    related_url=f"/appointments/{appointment.id}/",
                    notification_type="appointment"
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Notification created: {appointment.patient.get_full_name()}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Notification could not be created: {appointment.patient.get_full_name()} - Error: {str(e)}"
                ))
        
        self.stdout.write(self.style.SUCCESS(f"Total {len(appointments)} reminders sent.")) 