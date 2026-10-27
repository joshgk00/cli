# Experimental iPad 5 Wi-Fi (J71s) bring-up

This is research for the S8000 iPad 5 Wi-Fi (`iPad6,11`, J71sAP), not an
installation guide or a supported device adapter. The S8003 J71t variant needs
separate identification and testing.

On one J71s device, an unpatched Orchard kernel and the upstream J71s device
tree booted into a RAM-only system with a framebuffer, GPIO buttons, USB serial
and USB networking. A published Omarchy A root filesystem was served from the
host over an experimental read-only network block device. A temporary overlay
ran labwc and Quickshell on the physical 1536 x 2048 framebuffer; a terminal
and on-screen keyboard appeared, and software-generated keyboard input worked.
This did not test physical touch or boot the normal installed service lifecycle.
Neither the test image nor the network block-device prototype is an installer.

The Linux tree used in that test did not expose touchscreen or internal storage.
The Apple device tree identifies a `multi-touch,j72` touchscreen on SPI3 and
an S8000 PCIe controller. Its touch wiring and power provider differ from J71b;
do not copy the J71b initialization sequence. The PCIe tree also identifies a
BCM4355 Wi-Fi device, but PCIe, storage and Wi-Fi are not operational in this
test. The matching restore image includes multiple BCM4355 C0 firmware
candidates; their presence does not identify the correct board file or prove
compatibility.

Read-only Linux device metadata shows the Apple I2C adapter and an
`apple,angel-pmic` device bound to `simple-mfd-i2c`, with an RTC exposed.
No power-supply device appeared. The Apple tree identifies this PMU as
`pmu,d2365` and describes the touchscreen analog-power function through the
PMU; that does not establish a regulator mapping or a safe power sequence.

The iPadOS 16.7.16 restore image's `J71s.mtprops` contains profile `C1F15,1`,
packet type `Z2`, and a constructed packet with valid legacy length and
checksums. Its shape differs from the J71b firmware profile and cannot be fed
to the J71b converter unchanged. The matching iPadOS kernel metadata names an
`AppleMultitouchN1SPI` personality for `multi-touch,j72`. These observations do
not establish the power, calibration, firmware upload or input-report sequence.
`tools/j71s_touch_report.py` checks a locally extracted profile offline; it does
not operate the hardware.

`tools/j71s_adt_report.py` reports a limited subset of a private live Apple
device tree without printing identifiers or calibration data. Apple device trees
and calibration data can be unique to a device: keep the raw files private.
The report includes the length and whether any bytes are nonzero, but never the
contents or a hash. These properties do not verify that calibration is valid.
On the tested device the live field was 1,024 bytes and nonzero; the stock
restore image's tree contained a 31-byte field. The difference does not prove
what either field contains or whether it can be used by a Linux driver.
Do not commit firmware or raw captured data.
