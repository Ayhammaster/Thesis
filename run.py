import threading
from app import create_app

app = create_app()

# تشغيل مستمع MQTT في خيط خلفي (إن كانت paho-mqtt متوفرة)
try:
    from app.services.mqtt_subscriber import start_mqtt_listener
    threading.Thread(target=start_mqtt_listener, args=(app,), daemon=True).start()
    print("MQTT listener started")
except Exception as e:
    print(f"MQTT listener disabled: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
