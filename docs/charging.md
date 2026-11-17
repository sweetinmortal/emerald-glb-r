# Charging observations on the tested WFOMIXM device

The charging-control update was installed on slot A and the Lineage health services were verified across two boots with SELinux enforcing. The configured limit is 80 percent. A later reading recorded 79 percent with input_suspend set to 1. The controller uses a 10-point margin before resuming. These observations cover one Redmi Note 14S global.

Raw charge_control_limit values are thermal mitigation levels. Earlier notes incorrectly described values such as 12, 6 and 7 as amperes. The tested Xiaomi thermal daemon splits an encoded target such as 1207 into level 12 when thermal_message/screen_state is nonzero and level 7 when it is zero. Its active runtime profile is thermal-normal.conf. The charging-only profile is selected for charger boot mode.

The analyzed thermal daemon matches the executable on the tested phone. Its SHA-256 is `74e9aca016bcaf141b23821d9771163b5aecff40c6c1d13944e6bc90e208020f`. The observed state changes and kernel logs show that thermal mitigation operates. They do not establish why charging feels hotter than HyperOS under the owner's usual conditions.

A candidate MiCharge screen-state API was traced through the factory framework and service. That branch handles a connected USB camera-grip accessory and sends a HID report. It does not establish a missing charging policy for this device.

The remaining test requires the original charger and cable, recorded starting battery and ambient temperatures, state of charge, display state and workload. Input power and battery telemetry must be captured together. A comparable HyperOS measurement is still missing. No thermal-policy fix has been validated.

A further read-only capture on 2026-11-15 recorded 16 samples at 15-second intervals with the original charger. Battery level rose from 75 to 80 percent. At 80 percent, input_suspend changed from 0 to 1 and current changed from net charging to net discharge. Battery temperature started at 36.1 degrees Celsius and reached 37.6 degrees Celsius in this segment. The thermal screen_state node stayed at 0 and the raw mitigation level stayed at 3. The owner reported that the casing felt less hot. This confirms the cutoff in that session. It does not cover the warmer lower-charge part of a complete charging cycle.
