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
Linux also exposed an Apple backlight device. A small brightness-setting change
and restoration succeeded through sysfs; the visual change was not observed.

The Linux tree used in that test did not expose touchscreen or internal storage.
The Apple device tree identifies a `multi-touch,j72` touchscreen on SPI3 and
an S8000 PCIe controller. Its touch wiring and power provider differ from J71b;
do not copy the J71b initialization sequence. The PCIe tree also identifies a
BCM4355 Wi-Fi device, but PCIe, storage and Wi-Fi are not operational in this
test. The matching restore image includes multiple BCM4355 C0 firmware
candidates; their presence does not identify the correct board file or prove
compatibility.

An offline translation of the captured Apple tree locates the S8000 PCIe
configuration range at `0x610000000` and its first PCIe DART at `0x601008000`;
the NVMe MMU describes `0x601004000` and `0x601000000`. The J71b implementation
uses some of the same addresses, but also has T8010-specific initialization
and tuning. Address similarities alone do not establish S8000 compatibility or
make those register writes safe. No PCIe or NVMe registers were accessed.
The captured J71s tree lists PCIe port interrupts 244, 247, 250 and 253,
first DART interrupt 245, and NVMe MMU interrupt 246. The J71b experimental
tree uses different interrupt numbers, so its interrupt mapping must not be
copied to J71s.
An offline comparison using m1n1's 24-byte local-tunable record layout found
34 S8000 common-tuning records in the captured tree versus 38 entries in the
J71b T8010 driver's common-tuning table; the sequences are not identical.
This is not a complete compatibility analysis and does not validate applying
the S8000 records. Raw device-tree tuning data remains private.

Read-only Linux device metadata shows the Apple I2C adapter and an
`apple,angel-pmic` device bound to `simple-mfd-i2c`, with an RTC exposed.
No power-supply device appeared in the original baseline. The Apple tree identifies this PMU as
`pmu,d2365` and describes the touchscreen analog-power function through the
PMU; that does not establish a regulator mapping or a safe power sequence.
It also identifies a BQ27540 HDQ fuel gauge on UART5. The J71b project has
experimental HDQ support for that gauge family, but this device's interrupt
and pin wiring differ. In an experimental J71s RAM boot the UART and a battery
device registered, but all gauge readings returned I/O errors and the HDQ
transfer timed out. UART counters showed transmitted data but no receive data.
The bootloader's pre-mux pin state instead showed function 1. A later RAM boot
using function 1 and preserving a bootloader UART control bit produced plausible
status, capacity, voltage, current, temperature and charge readings on one
device across three checks. The gauge values have not been compared with iPadOS,
and charging is not supported by this test. The experiment is not currently
part of the adapter. A later host-served desktop test showed the same 24%
battery value in its top bar; it did not validate charging or an installed boot.
The host-served read-only desktop test was repeated on that experimental kernel:
the themed desktop, calendar, terminal and on-screen keyboard rendered, and
software-generated keyboard input appeared in the terminal. The test still did
not establish physical touch, internal storage or a normal installed boot.

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
