# ROADMAP
- Phase 1: Hardware Integration & Basic Pipeline Validation (Completed).
- Phase 2: Behavioral Optimization and Prompt Fine-tuning (Completed).
- Phase 3: Dashboard creation for vendors to manage inventory (Completed).
- Phase 4: Production deployment on embedded units with hardware-accelerated local inference.

### Phase 5: Privacy, Compliance, and User Agency Enhancements (Upcoming)
To ensure the system aligns with ethical guidelines and strict privacy laws (GDPR/CCPA), the following features will be prioritized in the next iteration:

1. **Explicit Opt-in Mechanism (Wake Word Integration):**
   - Replace unconsented proximity triggering with an explicit audio opt-in.
   - Integrate a lightweight, local wake-word engine (e.g., Porcupine or Snowboy). The system will remain entirely passive until a user actively initiates a session by saying "Hey Sirens."

2. **Enhanced Accessibility UI:**
   - Develop a visual companion display (e.g., using Pygame or a web dashboard) that provides real-time subtitles of the TTS output, aiding users who are hearing impaired or in excessively noisy environments.

3. **Strict Data Anonymization:**
   - Remove any facial embedding or repeat customer tracking features.
   - Ensure all visual attributes extracted by YOLO are immediately discarded from memory after the current, isolated session concludes.

4. **Transparent System Operations:**
   - Add visual indicators (e.g., LED lights) to clearly show when the microphone is active and when the system is processing data.
