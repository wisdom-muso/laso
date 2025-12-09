"""
WebSocket consumers for real-time telemedicine communication
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import TeleMedicineConsultation, TeleMedicineMessage, DoctorPatientMessage, MessageThread

User = get_user_model()
logger = logging.getLogger(__name__)


# WebRTC Code Removed - Replaced by Jitsi Meet
        self.room_group_name = f'consultation_{self.consultation_id}'
        self.user = self.scope['user']
        
        # Verify user can join this consultation
        if await self.can_join_consultation():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Update consultation status
            await self.update_user_joined()
            
            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name(),
                    'user_role': 'doctor' if self.user.is_doctor() else 'patient',
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            logger.info(f"User {self.user.id} joined consultation {self.consultation_id}")
        else:
            logger.warning(f"User {self.user.id} denied access to consultation {self.consultation_id}")
            await self.close()

    async def disconnect(self, close_code):
        # Update consultation status
        await self.update_user_left()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info(f"User {self.user.id} left consultation {self.consultation_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Route message based on type
            if message_type == 'webrtc_offer':
                await self.handle_webrtc_offer(data)
            elif message_type == 'webrtc_answer':
                await self.handle_webrtc_answer(data)
            elif message_type == 'ice_candidate':
                await self.handle_ice_candidate(data)
            elif message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'screen_share_start':
                await self.handle_screen_share(data)
            elif message_type == 'screen_share_stop':
                await self.handle_screen_share_stop(data)
            elif message_type == 'connection_quality':
                await self.handle_connection_quality(data)
            elif message_type == 'media_state':
                await self.handle_media_state(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    # WebRTC Signaling Handlers
    async def handle_webrtc_offer(self, data):
        """Handle WebRTC offer from peer"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_offer',
                'offer': data['offer'],
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )
        logger.info(f"WebRTC offer sent by user {self.user.id}")

    async def handle_webrtc_answer(self, data):
        """Handle WebRTC answer from peer"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_answer',
                'answer': data['answer'],
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )
        logger.info(f"WebRTC answer sent by user {self.user.id}")

    async def handle_ice_candidate(self, data):
        """Handle ICE candidate from peer"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'ice_candidate',
                'candidate': data['candidate'],
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_chat_message(self, data):
        """Handle chat message during consultation"""
        message_content = data.get('message', '').strip()
        if not message_content:
            return
            
        # Save message to database
        message_id = await self.save_chat_message(message_content)
        
        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_id,
                'message': message_content,
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_screen_share(self, data):
        """Handle screen sharing start"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_start',
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_screen_share_stop(self, data):
        """Handle screen sharing stop"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'screen_share_stop',
                'sender_id': self.user.id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_connection_quality(self, data):
        """Handle connection quality updates"""
        quality = data.get('quality', 'unknown')
        await self.update_connection_quality(quality)

    async def handle_media_state(self, data):
        """Handle media state changes (mute/unmute)"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'media_state_change',
                'sender_id': self.user.id,
                'video_enabled': data.get('video_enabled', True),
                'audio_enabled': data.get('audio_enabled', True),
                'timestamp': timezone.now().isoformat()
            }
        )

    # WebSocket message handlers (sent to client)
    async def webrtc_offer(self, event):
        """Send WebRTC offer to client (except sender)"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'offer': event['offer'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def webrtc_answer(self, event):
        """Send WebRTC answer to client (except sender)"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'answer': event['answer'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def ice_candidate(self, event):
        """Send ICE candidate to client (except sender)"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def chat_message(self, event):
        """Send chat message to client"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'is_own': event['sender_id'] == self.user.id
        }))

    async def user_joined(self, event):
        """Notify client that user joined"""
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'user_role': event['user_role'],
                'timestamp': event['timestamp']
            }))

    async def user_left(self, event):
        """Notify client that user left"""
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'timestamp': event['timestamp']
            }))

    async def screen_share_start(self, event):
        """Notify client that screen sharing started"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'screen_share_start',
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'timestamp': event['timestamp']
            }))

    async def screen_share_stop(self, event):
        """Notify client that screen sharing stopped"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'screen_share_stop',
                'sender_id': event['sender_id'],
                'timestamp': event['timestamp']
            }))

    async def media_state_change(self, event):
        """Notify client of media state changes"""
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'media_state_change',
                'sender_id': event['sender_id'],
                'video_enabled': event['video_enabled'],
                'audio_enabled': event['audio_enabled'],
                'timestamp': event['timestamp']
            }))

    # Database operations
    @database_sync_to_async
    def can_join_consultation(self):
        """Check if user can join this consultation"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            return consultation.can_join(self.user)
        except TeleMedicineConsultation.DoesNotExist:
            return False

    @database_sync_to_async
    def update_user_joined(self):
        """Update consultation when user joins"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            
            if self.user.is_doctor():
                consultation.doctor_joined_at = timezone.now()
            else:
                consultation.patient_joined_at = timezone.now()
            
            # Update status if both joined
            if consultation.doctor_joined_at and consultation.patient_joined_at:
                consultation.status = 'in_progress'
                if not consultation.actual_start_time:
                    consultation.actual_start_time = timezone.now()
            
            consultation.save()
            
        except TeleMedicineConsultation.DoesNotExist:
            pass

    @database_sync_to_async
    def update_user_left(self):
        """Update consultation when user leaves"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            
            # If consultation was in progress, mark as completed
            if consultation.status == 'in_progress':
                consultation.end_time = timezone.now()
                consultation.status = 'completed'
                
                # Calculate duration
                if consultation.actual_start_time:
                    duration = consultation.end_time - consultation.actual_start_time
                    consultation.duration_minutes = int(duration.total_seconds() / 60)
                
                consultation.save()
                
        except TeleMedicineConsultation.DoesNotExist:
            pass

    @database_sync_to_async
    def save_chat_message(self, content):
        """Save chat message to database"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            message = TeleMedicineMessage.objects.create(
                consultation=consultation,
                sender=self.user,
                content=content,
                message_type='text'
            )
            return message.id
        except TeleMedicineConsultation.DoesNotExist:
            return None

    @database_sync_to_async
    def update_connection_quality(self, quality):
        """Update connection quality in database"""
        try:
            consultation = TeleMedicineConsultation.objects.get(id=self.consultation_id)
            consultation.connection_quality = quality
            consultation.save()
        except TeleMedicineConsultation.DoesNotExist:
            pass


class DirectMessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for direct messaging between doctors and patients
    """
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Only doctors and patients can use direct messaging
        if not (self.user.is_doctor() or self.user.is_patient()):
            await self.close()
            return
        
        # Create user-specific room
        self.room_name = f'user_{self.user.id}_messages'
        self.room_group_name = f'messages_{self.user.id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.id} connected to direct messaging")
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User {self.user.id} disconnected from direct messaging")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            elif message_type == 'start_video_call':
                await self.handle_start_video_call(data)
            elif message_type == 'start_audio_call':
                await self.handle_start_audio_call(data)
            elif message_type == 'call_response':
                await self.handle_call_response(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    async def handle_send_message(self, data):
        """Handle sending a direct message"""
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        is_urgent = data.get('is_urgent', False)
        
        if not content or not recipient_id:
            return
        
        # Save message to database
        message_data = await self.save_direct_message(
            recipient_id, content, message_type, is_urgent
        )
        
        if message_data:
            # Send to recipient
            recipient_room = f'messages_{recipient_id}'
            await self.channel_layer.group_send(
                recipient_room,
                {
                    'type': 'new_message',
                    'message': message_data,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Send confirmation to sender
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message': message_data,
                'timestamp': timezone.now().isoformat()
            }))
    
    async def handle_mark_read(self, data):
        """Handle marking messages as read"""
        message_ids = data.get('message_ids', [])
        await self.mark_messages_read(message_ids)
    
    async def handle_start_video_call(self, data):
        """Handle starting a video call"""
        recipient_id = data.get('recipient_id')
        if not recipient_id:
            return
        
        # Create call session
        call_session_id = await self.create_call_session(recipient_id, 'video')
        
        if call_session_id:
            # Send call request to recipient
            recipient_room = f'messages_{recipient_id}'
            await self.channel_layer.group_send(
                recipient_room,
                {
                    'type': 'incoming_call',
                    'call_type': 'video',
                    'call_session_id': str(call_session_id),
                    'caller_id': self.user.id,
                    'caller_name': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def handle_start_audio_call(self, data):
        """Handle starting an audio call"""
        recipient_id = data.get('recipient_id')
        if not recipient_id:
            return
        
        # Create call session
        call_session_id = await self.create_call_session(recipient_id, 'audio')
        
        if call_session_id:
            # Send call request to recipient
            recipient_room = f'messages_{recipient_id}'
            await self.channel_layer.group_send(
                recipient_room,
                {
                    'type': 'incoming_call',
                    'call_type': 'audio',
                    'call_session_id': str(call_session_id),
                    'caller_id': self.user.id,
                    'caller_name': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    async def handle_call_response(self, data):
        """Handle call response (accept/decline)"""
        call_session_id = data.get('call_session_id')
        response = data.get('response')  # 'accepted' or 'declined'
        caller_id = data.get('caller_id')
        
        if not all([call_session_id, response, caller_id]):
            return
        
        # Update call status
        await self.update_call_status(call_session_id, response)
        
        # Notify caller
        caller_room = f'messages_{caller_id}'
        await self.channel_layer.group_send(
            caller_room,
            {
                'type': 'call_response',
                'call_session_id': call_session_id,
                'response': response,
                'responder_id': self.user.id,
                'responder_name': self.user.get_full_name(),
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        recipient_id = data.get('recipient_id')
        is_typing = data.get('is_typing', False)
        
        if not recipient_id:
            return
        
        # Send typing indicator to recipient
        recipient_room = f'messages_{recipient_id}'
        await self.channel_layer.group_send(
            recipient_room,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'is_typing': is_typing,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    # WebSocket message handlers (sent to client)
    async def new_message(self, event):
        """Send new message to client"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))
    
    async def incoming_call(self, event):
        """Send incoming call notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'call_type': event['call_type'],
            'call_session_id': event['call_session_id'],
            'caller_id': event['caller_id'],
            'caller_name': event['caller_name'],
            'timestamp': event['timestamp']
        }))
    
    async def call_response(self, event):
        """Send call response to client"""
        await self.send(text_data=json.dumps({
            'type': 'call_response',
            'call_session_id': event['call_session_id'],
            'response': event['response'],
            'responder_id': event['responder_id'],
            'responder_name': event['responder_name'],
            'timestamp': event['timestamp']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to client"""
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing'],
            'timestamp': event['timestamp']
        }))
    
    # Database operations
    @database_sync_to_async
    def save_direct_message(self, recipient_id, content, message_type, is_urgent):
        """Save direct message to database"""
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # Determine doctor and patient
            if self.user.is_doctor():
                doctor = self.user
                patient = recipient
            else:
                doctor = recipient
                patient = self.user
            
            # Create or get message thread
            thread, created = MessageThread.objects.get_or_create(
                doctor=doctor,
                patient=patient
            )
            
            # Create message
            message = DoctorPatientMessage.objects.create(
                doctor=doctor,
                patient=patient,
                sender=self.user,
                message_type=message_type,
                content=content,
                is_urgent=is_urgent
            )
            
            # Update thread
            thread.last_message_at = timezone.now()
            thread.update_unread_count(recipient)
            thread.save()
            
            return {
                'id': message.id,
                'content': message.content,
                'message_type': message.message_type,
                'is_urgent': message.is_urgent,
                'created_at': message.created_at.isoformat(),
                'sender_id': message.sender.id,
                'sender_name': message.sender.get_full_name(),
                'recipient_id': recipient.id,
                'recipient_name': recipient.get_full_name(),
            }
            
        except User.DoesNotExist:
            logger.error(f"Recipient {recipient_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return None
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read"""
        try:
            DoctorPatientMessage.objects.filter(
                id__in=message_ids
            ).exclude(
                sender=self.user
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}")
    
    @database_sync_to_async
    def create_call_session(self, recipient_id, call_type):
        """Create a call session"""
        try:
            import uuid
            recipient = User.objects.get(id=recipient_id)
            
            # Determine doctor and patient
            if self.user.is_doctor():
                doctor = self.user
                patient = recipient
            else:
                doctor = recipient
                patient = self.user
            
            call_session_id = uuid.uuid4()
            
            # Create call request message
            message = DoctorPatientMessage.objects.create(
                doctor=doctor,
                patient=patient,
                sender=self.user,
                message_type=f'{call_type}_call_request',
                content=f'{call_type.title()} call request',
                call_session_id=call_session_id,
                call_status='pending'
            )
            
            return call_session_id
            
        except User.DoesNotExist:
            logger.error(f"Recipient {recipient_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error creating call session: {str(e)}")
            return None
    
    @database_sync_to_async
    def update_call_status(self, call_session_id, status):
        """Update call status"""
        try:
            DoctorPatientMessage.objects.filter(
                call_session_id=call_session_id
            ).update(call_status=status)
        except Exception as e:
            logger.error(f"Error updating call status: {str(e)}")