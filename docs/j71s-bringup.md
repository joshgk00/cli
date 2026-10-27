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
device across three checks. After iPadOS reported 100% charge, Linux reported
90%; the cause and accuracy of the readings remain unresolved. Charging is not
supported by this test. The experiment is not currently
part of the adapter. A later host-served desktop test showed the same 24%
battery value in its top bar; it did not validate charging or an installed boot.
An additional RAM-only diagnostic boot counted HDQ response symbols in the
range where the experimental decoder and TI's UART example differ. Two fresh
sampling rounds each reported zero such symbols across nine transfers. This
does not validate the gauge profile, the remaining decoding, or the battery
percentage; it only means this particular ambiguity was not observed in those
samples.
Immediately before restarting into iPadOS, Linux reported 88% and discharging;
the user then observed 100% in iPadOS. This closer comparison confirms a
displayed-value discrepancy on this device, but does not identify its cause.
The experimental Linux profile returns the gauge's state-of-charge register
directly; the comparison does not establish how iPadOS calculates its display.
In that iPadOS session, its battery service also reported 100%, external power
connected, external charging capability false, and not charging. This single
observation at a displayed 100% does not establish why charging capability was
reported false or how the port behaves with a less-full battery.
Moving the connected, unlocked iPad to the computer's other USB port produced
the same iPadOS battery-service fields at a displayed 100%. This does not
measure either port's output or rule out a cable or negotiation issue.
The subsequent diagnostic Linux boot on that second port also reported battery
discharge; its capacity reading was 87%. Charging remains unverified in Linux.
The captured Apple tree identifies a `tristar,cbtl1610` Lightning controller and
a `charger,k48` node. The J71s test did not expose a charger power-supply device
and reported battery discharge while USB was connected. These identifiers do
not establish a safe input-current limit or charging-control sequence; the
offline report does not print battery IDs, Lightning identifiers, charge
curves or raw charger functions.
An older iPad mini Linux project has a charger driver for a different D1946
PMU; its current-limit register and behavior cannot be assumed to apply to the
J71s D2365. No charger-control registers have been written in this experiment.
On the tested host, the RAM gadget enumerated at USB 2 high speed (480 Mb/s)
and advertised `bMaxPower` 500 mA, matching its kernel's
`CONFIG_USB_GADGET_VBUS_DRAW=500`. This is the device configuration's declared
maximum, not a measurement of host-port output or actual input current. The
[USB-IF standard-port rules](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies)
limit a USB 2 peripheral on a standard downstream port to 500 mA (2.5 W at 5 V).
[Apple lists a 12 W adapter](https://support.apple.com/en-us/HT210133) for the
iPad 5 in many regions, with 10 W in some. The battery gauge reported negative
current during this test. These facts make limited USB power a plausible
contributor, but do not distinguish host capacity from device-side charging
configuration; an actual inline measurement and hardware-specific charger
research would be needed. Do not infer that 10 or 12 W is a minimum required
to charge.
For another host, `python3 tools/usb_power_report.py /sys/bus/usb/devices/DEVICE`
reports the selected USB device's configuration and link speed without reading
identifiers; replace `DEVICE` with its sysfs directory. It cannot measure the
host's output or the current entering the iPad.
The host's Apple MFi fast-charge driver was loaded but not bound to this RAM
gadget (`05ac:4142`). The [Linux driver](https://github.com/torvalds/linux/blob/master/drivers/usb/misc/apple-mfi-fastcharge.c)
matches a different product-ID range and uses a device protocol. Changing the
identifier alone would not implement that protocol or establish safe charging.
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
The independently documented [J172 touch implementation](https://github.com/Pauli1Go/HoolockLinux-bringup-docs/blob/c9d02db/docs/touch.md)
is a useful architectural reference: its A10 implementation combines a touch
clock, SmartIO DMA, SPI controller and Z2 protocol state machine. It is tested
on a different board and uses HBPP14 firmware and board-specific power wiring;
neither its sequence nor its GPIO numbers establish a safe J71s implementation.
Separate [J81 N1 touchscreen research](https://github.com/mattonik/ipad-nixos/blob/b94d42f78e04c5465e290340a5b6879bbc5956b6/research/2026-10-11-touch-no-ack-analysis.md)
examines an older N1 SPI implementation and identifies bit order and sequencing
as potential causes of failed firmware acknowledgment on that other device.
J81 uses a different PMU and wiring; its power and SPI settings require
independent verification before applying them to J71s. Its observed packet
behavior is a reference, not a validated J71s boot procedure.
As an offline feasibility check, that project's patches `0007`, `0096`, and
`0098` at revision `b94d42f78e04c5465e290340a5b6879bbc5956b6` were applied
in order to an isolated Hoolock kernel checkout at
`6831bc701a6ce059e71e5aaa9488c9195bea6927`; `drivers/spi/spi-apple.o` built
with the J71s kernel configuration and Orchard's LLVM 19 toolchain. The last
patch applied with line offsets. This compiled only a driver object, not a
bootable kernel, and did not exercise SPI hardware or establish J71s clock,
power, pinmux, or touch compatibility. The patches are not part of this branch.
`tools/j71s_touch_report.py` checks a locally extracted profile offline; it does
not operate the hardware.
`tools/j71s_touch_personality.py` summarizes an allowlist of static J71s
personality metadata from a local `ipsw kernel kexts --json` report. Obtain the
kernelcache from a separately verified matching restore image. The utility
does not verify the restore image, inspect live values, generate firmware, or
establish a safe power-up sequence.

`tools/j71s_adt_report.py` reports a limited subset of a private live Apple
device tree without printing identifiers or calibration data. Apple device trees
and calibration data can be unique to a device: keep the raw files private.
The report includes the length and whether any bytes are nonzero, but never the
contents or a hash. These properties do not verify that calibration is valid.
On the tested device the live field was 1,024 bytes and nonzero; the stock
restore image's tree contained a 31-byte field. The difference does not prove
what either field contains or whether it can be used by a Linux driver.
Do not commit firmware or raw captured data.
