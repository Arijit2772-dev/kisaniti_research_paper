# Hardware — architecture and simulation (phase R5)

**Goal for Paper 1:** a clear hardware architecture plus a working **Wokwi** simulation that sends real MQTT messages into the KisanNiti pipeline. A physical bench test is optional for Paper 1 and required for Paper 2.

**Architecture (decision D1 pending; recommended):**

```text
SHT30 probe in grain ─I²C (SDA GPIO21, SCL GPIO22, 4.7 kΩ pull-ups)─► ESP32-WROOM-32
   ─► Wi-Fi (phone hotspot) ─► MQTT over TLS ─► ingestion service ─► SensorReading
   ─► storage rule (STORAGE-DEMO-0.1) ─► StorageAssessment ─► planner / dashboard
```

**Wokwi plan:**
1. Check whether the Wokwi parts list includes an SHT3x sensor.
   - If yes, use it.
   - If not, build a small Wokwi custom chip that answers SHT3x I²C commands.
   - Fallback: use DHT22 and state plainly that it is a simulation stand-in.
2. Firmware (Arduino framework, pinned version):
   - read every 5 minutes (shortened in simulation);
   - each message carries device ID, boot ID and sequence number;
   - publish JSON matching the SensorReading contract;
   - reconnect and buffer.
3. Use the Wokwi-GUEST network to publish to a test MQTT broker. A public test broker is acceptable for the simulation only, with no personal data; a TLS broker is used for the real deployment.
4. Record screenshots, the serial log and the matching backend records.

**Files:**
- `wokwi/`: `diagram.json`, `wokwi.toml`, the custom chip if needed;
- `firmware/`: source and README with versions;
- the architecture figure for the paper.

**Real kit:** see the [hardware list](../../kisaniti/docs/HARDWARE_CURRENT.md) and the circuit drawing in the planning folder.
