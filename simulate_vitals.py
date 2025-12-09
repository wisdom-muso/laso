#!/usr/bin/env python3
"""
Vitals Simulator for Testing Real-time Dashboard
Simulates patient vital signs and sends updates via WebSocket
"""
import os
import sys
import django
import asyncio
import json
import random
from datetime import datetime, timedelta
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from treatments.models_vitals import VitalSign, VitalSignAlert

User = get_user_model()


class VitalsSimulator:
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.running = False
        
    async def simulate_patient_vitals(self, patient_id, duration_minutes=10):
        """Simulate vitals for a specific patient"""
        try:
            patient = await sync_to_async(User.objects.get)(id=patient_id, user_type='patient')
            print(f"Starting vitals simulation for {patient.get_full_name()}")
            
            self.running = True
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            while self.running and datetime.now() < end_time:
                # Generate realistic vital signs
                vitals_data = self.generate_realistic_vitals()
                
                # Save to database
                vital_sign = await self.save_vital_sign(patient, vitals_data)
                
                # Send WebSocket update
                await self.send_vitals_update(patient_id, vital_sign)
                
                # Check for alerts
                await self.check_and_send_alerts(vital_sign)
                
                print(f"Updated vitals for {patient.get_full_name()}: BP {vitals_data['systolic_bp']}/{vitals_data['diastolic_bp']}, HR {vitals_data['heart_rate']}")
                
                # Wait before next update (30 seconds to 2 minutes)
                await asyncio.sleep(random.randint(30, 120))
                
        except User.DoesNotExist:
            print(f"Patient with ID {patient_id} not found")
        except Exception as e:
            print(f"Error in simulation: {e}")
    
    def generate_realistic_vitals(self):
        """Generate realistic vital signs with some variation"""
        # Base values (normal ranges)
        base_systolic = random.randint(110, 130)
        base_diastolic = random.randint(70, 85)
        base_hr = random.randint(65, 85)
        base_temp = round(random.uniform(36.1, 37.2), 1)
        base_o2 = random.randint(96, 100)
        
        # Add some variation (occasionally abnormal values)
        if random.random() < 0.2:  # 20% chance of elevated BP
            base_systolic += random.randint(20, 40)
            base_diastolic += random.randint(10, 20)
        
        if random.random() < 0.15:  # 15% chance of elevated HR
            base_hr += random.randint(20, 35)
        
        if random.random() < 0.1:  # 10% chance of fever
            base_temp += random.uniform(1.0, 2.5)
        
        if random.random() < 0.05:  # 5% chance of low O2
            base_o2 -= random.randint(5, 15)
        
        return {
            'systolic_bp': min(200, base_systolic),
            'diastolic_bp': min(120, base_diastolic),
            'heart_rate': min(150, base_hr),
            'temperature': min(42.0, base_temp),
            'oxygen_saturation': max(85, base_o2),
            'weight': round(random.uniform(60, 90), 1),
            'respiratory_rate': random.randint(12, 20),
        }
    
    @sync_to_async
    def save_vital_sign(self, patient, vitals_data):
        """Save vital sign to database"""
        vital_sign = VitalSign.objects.create(
            patient=patient,
            **vitals_data
        )
        return vital_sign
    
    async def send_vitals_update(self, patient_id, vital_sign):
        """Send vitals update via WebSocket"""
        if not self.channel_layer:
            return
        
        vitals_data = {
            'id': vital_sign.id,
            'systolic_bp': vital_sign.systolic_bp,
            'diastolic_bp': vital_sign.diastolic_bp,
            'blood_pressure_display': vital_sign.blood_pressure_display,
            'heart_rate': vital_sign.heart_rate,
            'temperature': float(vital_sign.temperature) if vital_sign.temperature else None,
            'oxygen_saturation': vital_sign.oxygen_saturation,
            'overall_risk_level': vital_sign.overall_risk_level,
            'bp_category': vital_sign.bp_category,
            'recorded_at': vital_sign.recorded_at.isoformat(),
        }
        
        # Send to patient's room
        await self.channel_layer.group_send(
            f'vitals_patient_{patient_id}',
            {
                'type': 'vitals_update',
                'patient_id': patient_id,
                'data': vitals_data,
                'message': 'Vitals updated'
            }
        )
        
        # Send to medical staff room
        await self.channel_layer.group_send(
            'vitals_medical_staff',
            {
                'type': 'vitals_update',
                'patient_id': patient_id,
                'data': vitals_data,
                'message': f'Patient {patient_id} vitals updated'
            }
        )
    
    async def check_and_send_alerts(self, vital_sign):
        """Check for critical vitals and send alerts"""
        alerts = []
        
        # Check blood pressure
        if vital_sign.systolic_bp > 180 or vital_sign.diastolic_bp > 120:
            alerts.append({
                'type': 'high_bp',
                'severity': 'critical',
                'message': f'Critical blood pressure: {vital_sign.blood_pressure_display} mmHg'
            })
        elif vital_sign.systolic_bp > 140 or vital_sign.diastolic_bp > 90:
            alerts.append({
                'type': 'high_bp',
                'severity': 'high',
                'message': f'High blood pressure: {vital_sign.blood_pressure_display} mmHg'
            })
        
        # Check heart rate
        if vital_sign.heart_rate > 120:
            alerts.append({
                'type': 'high_hr',
                'severity': 'high',
                'message': f'High heart rate: {vital_sign.heart_rate} bpm'
            })
        elif vital_sign.heart_rate < 50:
            alerts.append({
                'type': 'low_hr',
                'severity': 'high',
                'message': f'Low heart rate: {vital_sign.heart_rate} bpm'
            })
        
        # Check temperature
        if vital_sign.temperature and vital_sign.temperature > 39.0:
            alerts.append({
                'type': 'high_temp',
                'severity': 'high',
                'message': f'High fever: {vital_sign.temperature}°C'
            })
        
        # Check oxygen saturation
        if vital_sign.oxygen_saturation and vital_sign.oxygen_saturation < 90:
            alerts.append({
                'type': 'low_o2',
                'severity': 'critical',
                'message': f'Low oxygen saturation: {vital_sign.oxygen_saturation}%'
            })
        
        # Send alerts
        for alert_data in alerts:
            await self.send_alert(vital_sign, alert_data)
    
    @sync_to_async
    def create_alert(self, vital_sign, alert_data):
        """Create alert in database"""
        return VitalSignAlert.objects.create(
            vital_sign=vital_sign,
            alert_type=alert_data['type'],
            severity=alert_data['severity'],
            message=alert_data['message']
        )
    
    async def send_alert(self, vital_sign, alert_data):
        """Send alert via WebSocket"""
        if not self.channel_layer:
            return
        
        # Create alert in database
        alert = await self.create_alert(vital_sign, alert_data)
        
        alert_message = {
            'id': alert.id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'message': alert.message,
            'patient_name': vital_sign.patient.get_full_name(),
            'patient_id': vital_sign.patient.id,
            'created_at': alert.created_at.isoformat(),
            'vital_sign_id': vital_sign.id
        }
        
        # Send to alerts room
        await self.channel_layer.group_send(
            'vitals_alerts',
            {
                'type': 'new_alert',
                'alert_data': alert_message,
                'message': 'New vitals alert'
            }
        )
        
        print(f"ALERT: {alert.message} for {vital_sign.patient.get_full_name()}")
    
    def stop(self):
        """Stop the simulation"""
        self.running = False


async def main():
    """Main function to run the simulator"""
    if len(sys.argv) < 2:
        print("Usage: python simulate_vitals.py <patient_id> [duration_minutes]")
        print("Example: python simulate_vitals.py 1 5")
        return
    
    try:
        patient_id = int(sys.argv[1])
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        
        simulator = VitalsSimulator()
        
        print(f"Starting vitals simulation for patient {patient_id} for {duration} minutes")
        print("Press Ctrl+C to stop")
        
        try:
            await simulator.simulate_patient_vitals(patient_id, duration)
        except KeyboardInterrupt:
            print("\nStopping simulation...")
            simulator.stop()
        
    except ValueError:
        print("Error: Patient ID must be a number")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    asyncio.run(main())
