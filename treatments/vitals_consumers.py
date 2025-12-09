import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from treatments.models_vitals import VitalSign
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class VitalsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Create a group name based on user ID
        self.group_name = f"vitals_{self.user.id}"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial vitals data
        await self.send_vitals_update()

    async def disconnect(self, close_code):
        # Leave the group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_vitals':
                await self.send_vitals_update()
            elif message_type == 'add_vital':
                await self.add_vital_sign(data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data'
            }))

    async def add_vital_sign(self, data):
        """Add a new vital sign record"""
        try:
            vital_data = data.get('vital_data', {})
            
            # Validate required fields
            required_fields = ['systolic_bp', 'diastolic_bp', 'heart_rate']
            for field in required_fields:
                if field not in vital_data:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'Missing required field: {field}'
                    }))
                    return
            
            # Create the vital sign record
            vital = await self.create_vital_sign(vital_data)
            
            # Send update to all connected clients for this user
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'vitals_update',
                    'vital': await self.serialize_vital(vital)
                }
            )
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def create_vital_sign(self, vital_data):
        """Create a new vital sign record in the database"""
        return VitalSign.objects.create(
            patient=self.user,
            recorded_by=self.user,  # Self-recorded
            systolic_bp=int(vital_data['systolic_bp']),
            diastolic_bp=int(vital_data['diastolic_bp']),
            heart_rate=int(vital_data['heart_rate']),
            temperature=float(vital_data.get('temperature', 0)) if vital_data.get('temperature') else None,
            oxygen_saturation=int(vital_data.get('oxygen_saturation', 0)) if vital_data.get('oxygen_saturation') else None,
            weight=float(vital_data.get('weight', 0)) if vital_data.get('weight') else None,
            height=float(vital_data.get('height', 0)) if vital_data.get('height') else None,
            notes=vital_data.get('notes', ''),
            recorded_at=timezone.now()
        )

    @database_sync_to_async
    def get_latest_vitals(self):
        """Get the latest vital signs for the user"""
        try:
            return list(VitalSign.objects.filter(
                patient=self.user
            ).order_by('-recorded_at')[:10])
        except:
            return []

    @database_sync_to_async
    def serialize_vital(self, vital):
        """Serialize a vital sign object"""
        return {
            'id': vital.id,
            'systolic_bp': vital.systolic_bp,
            'diastolic_bp': vital.diastolic_bp,
            'heart_rate': vital.heart_rate,
            'temperature': float(vital.temperature) if vital.temperature else None,
            'oxygen_saturation': vital.oxygen_saturation,
            'weight': float(vital.weight) if vital.weight else None,
            'height': float(vital.height) if vital.height else None,
            'notes': vital.notes,
            'recorded_at': vital.recorded_at.isoformat(),
            'blood_pressure_display': f"{vital.systolic_bp}/{vital.diastolic_bp}",
            'risk_level': vital.get_bp_risk_level(),
        }

    async def send_vitals_update(self):
        """Send vitals update to the client"""
        vitals = await self.get_latest_vitals()
        serialized_vitals = []
        
        for vital in vitals:
            serialized_vitals.append(await self.serialize_vital(vital))
        
        await self.send(text_data=json.dumps({
            'type': 'vitals_data',
            'vitals': serialized_vitals,
            'latest_vital': serialized_vitals[0] if serialized_vitals else None,
            'timestamp': timezone.now().isoformat()
        }))

    # Handle group messages
    async def vitals_update(self, event):
        """Handle vitals update from group"""
        await self.send(text_data=json.dumps({
            'type': 'new_vital',
            'vital': event['vital'],
            'timestamp': timezone.now().isoformat()
        }))


class DoctorVitalsConsumer(AsyncWebsocketConsumer):
    """Consumer for doctors to monitor patient vitals"""
    
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated or self.user.user_type != 'doctor':
            await self.close()
            return
            
        self.patient_id = self.scope['url_route']['kwargs']['patient_id']
        
        # Verify doctor has access to this patient
        has_access = await self.verify_doctor_access()
        if not has_access:
            await self.close()
            return
            
        # Create a group name for this patient's vitals
        self.group_name = f"vitals_{self.patient_id}"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial vitals data
        await self.send_patient_vitals()

    async def disconnect(self, close_code):
        # Leave the group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    @database_sync_to_async
    def verify_doctor_access(self):
        """Verify doctor has access to monitor this patient"""
        try:
            # Check if doctor has any appointments with this patient
            from appointments.models import Appointment
            return Appointment.objects.filter(
                doctor=self.user,
                patient_id=self.patient_id
            ).exists()
        except:
            return False

    @database_sync_to_async
    def get_patient_vitals(self):
        """Get patient's vital signs"""
        try:
            return list(VitalSign.objects.filter(
                patient_id=self.patient_id
            ).order_by('-recorded_at')[:20])
        except:
            return []

    async def send_patient_vitals(self):
        """Send patient vitals to the doctor"""
        vitals = await self.get_patient_vitals()
        serialized_vitals = []
        
        for vital in vitals:
            serialized_vitals.append(await self.serialize_vital(vital))
        
        await self.send(text_data=json.dumps({
            'type': 'patient_vitals',
            'patient_id': self.patient_id,
            'vitals': serialized_vitals,
            'latest_vital': serialized_vitals[0] if serialized_vitals else None,
            'timestamp': timezone.now().isoformat()
        }))

    @database_sync_to_async
    def serialize_vital(self, vital):
        """Serialize a vital sign object"""
        return {
            'id': vital.id,
            'systolic_bp': vital.systolic_bp,
            'diastolic_bp': vital.diastolic_bp,
            'heart_rate': vital.heart_rate,
            'temperature': float(vital.temperature) if vital.temperature else None,
            'oxygen_saturation': vital.oxygen_saturation,
            'weight': float(vital.weight) if vital.weight else None,
            'height': float(vital.height) if vital.height else None,
            'notes': vital.notes,
            'recorded_at': vital.recorded_at.isoformat(),
            'blood_pressure_display': f"{vital.systolic_bp}/{vital.diastolic_bp}",
            'risk_level': vital.get_bp_risk_level(),
        }

    # Handle group messages
    async def vitals_update(self, event):
        """Handle vitals update from group"""
        await self.send(text_data=json.dumps({
            'type': 'new_vital',
            'vital': event['vital'],
            'timestamp': timezone.now().isoformat()
        }))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_vitals':
                await self.send_patient_vitals()
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data'
            }))