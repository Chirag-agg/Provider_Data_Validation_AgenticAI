@echo off
cd src
python -c "from provider_data_validation.crews.drift_monitoring_crew.drift_monitoring_crew import DriftMonitoringCrew; print('Testing Drift Monitoring for Dr Shalini Rao...'); crew = DriftMonitoringCrew(); result = crew.crew().kickoff(inputs={'provider_name': 'Dr Shalini Rao'}); print('\nResult:'); print(result)"
cd ..
