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
the NVMe MMU describes `0x601004000` and `0x601000000`. An independent m1n1
translation shows those same two windows in the PCIe controller's resource
list, in the opposite order. Their overlap is a device-tree description, not
proof of their register functions or safety. The J71b implementation
uses some of the same addresses, but also has T8010-specific initialization
and tuning. Address similarities alone do not establish S8000 compatibility or
make those register writes safe. No PCIe or NVMe registers were accessed.
The separate [J81 PCIe investigation](https://github.com/mattonik/ipad-nixos/blob/b94d42f78e04c5465e290340a5b6879bbc5956b6/research/t7000-pcie-hardware-findings.md)
reports that enabling its DART device caused a boot hang. J81 is a different
SoC; this is not a prediction for J71s, but is evidence that merely enabling a
similar-looking DART node is not a validated way to bring up storage.
The captured J71s tree lists PCIe port interrupts 244, 247, 250 and 253,
first DART interrupt 245, and NVMe MMU interrupt 246. The J71b experimental
tree uses different interrupt numbers, so its interrupt mapping must not be
copied to J71s.
The Apple tree places an `s3e` node under bridge 0, which has an `nvme-mode`
marker and maximum link-speed value 2; the BCM4355 Wi-Fi node is under bridge 1,
with maximum link-speed value 1. These are topology descriptions and limits,
not evidence that either link has trained or that storage access is safe.
The captured tree also associates bridge 0's `function-dart_force_active`
with `dart-apcie0` and bridge 1's corresponding function with `dart-apcie1`.
This identifies relationships between the bridge and its DART; it does not
explain how to make the DART available or establish a safe register sequence.
An offline comparison using m1n1's 24-byte local-tunable record layout found
34 S8000 common-tuning records in the captured tree versus 38 entries in the
J71b T8010 driver's common-tuning table; the sequences are not identical.
This is not a complete compatibility analysis and does not validate applying
the S8000 records. Raw device-tree tuning data remains private.
Offline decoding of the J71s PCIe node's six power gate IDs found AUX, REF,
and LINK0–LINK3 at the same PMGR offsets as the named S8000 Linux power
domains. The Apple tree gives the link gates a PCIe parent, also matching the
Linux parent relationships. These matches are evidence for candidate power
domain descriptions, not proof that a PCIe or NVMe initialization sequence
is safe or complete. The offline comparison accessed no hardware registers.
In a later DART0-only RAM boot, the PCIe power domain was enabled and the
experimental `apple-dart` driver reset and initialized DART0 with 4 KiB pages
and four streams. USB serial remained available; no PCIe host or NVMe block
device appeared. The test did not connect an IOMMU consumer or perform a DMA
translation and does not establish internal storage support.
In a follow-up boot, a software-only consumer joined IOMMU group 0 and reported
a DMA domain, but the DART driver logged a busy-bit timeout for an invalidate
command on stream 0. The pinned driver's translation setup ignores that return
value. Therefore the registered domain is not evidence of working translation;
no physical DMA or internal storage access occurred.
A later isolated boot using an all-stream invalidate also timed out. Five
DART0 register offsets subsequently read as all ones. This may indicate that
the hardware block is unavailable, but does not establish when that condition
began or its cause. In particular, neither the earlier reset return nor the
reported busy and translation-enable bits establish that the DART was
responding normally.

Read-only Linux device metadata shows the Apple I2C adapter and an
`apple,angel-pmic` device bound to `simple-mfd-i2c`, with an RTC exposed.
No power-supply device appeared in the original baseline. The Apple tree identifies this PMU as
`pmu,d2365` and describes the touchscreen analog-power function through the
PMU; that does not establish a regulator mapping or a safe power sequence.
The matching iPadOS kernelcache contains D2365-specific LDO function class and
diagnostic strings, consistent with the Apple tree's PMU-mediated analog
power function. Strings alone do not identify the rail, voltage, register map,
or enable sequence, and no PMU power-control registers were accessed.
An offline inspection of the matching iPadOS 16.7.16 kernelcache found that
the D2365 `_setLDO` routine indexes a 12-byte-per-entry descriptor table and
uses fields in the selected entry for a masked register update. The J71s
touch power function's raw argument is `0x21f`. Applying the separately
investigated J81 low-byte index interpretation suggests descriptor 31; that
entry suggests enable register `0x31c`, mask `0x01`. The D2365 argument
interpretation and this rail's identity, voltage and live register semantics
remain unverified. `tools/j71s_pmu_research.py` reports only this candidate
from the exact kernelcache hash and never accesses the device. Do not write or
read candidate PMU registers based on this static result alone.
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
The Orchard hardware repository also contains a [J71b charging policy](https://github.com/OrchardLinux/hardware/blob/b8d43b2/kernel/modules/j71b/power/j71b_charge_policy.c)
for an `apple,angel-pmic`. It is restricted to J71b and uses battery, PMIC
state and handoff checks before a short charging lease. This is a closer PMU
reference than the older D1946 driver, but its register assumptions, source
detection, limits and safety behavior have not been validated on J71s. It must
not be loaded or adapted merely by removing its board guard.
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
Both the J81 research and the captured J71s tree identify SPI3 as
`spi-1,samsung`; the J71s tree also reports SPI version 1. That shared label
motivates testing the older SPI driver but does not prove identical clocks,
register behavior, or board wiring.
The J71s tree reports SPI3 clock-gate word `0x4d` and clock-ID word `0x130`;
the J81 research reports the same gate word but a different clock ID (`0x12e`).
These are Apple tree values, not validated Linux clock configuration or a
license to copy a clock rate or write PMGR registers.
Using the low-byte table lookup proposed in the
[J81 SPI clock investigation](https://github.com/mattonik/ipad-nixos/blob/b94d42f78e04c5465e290340a5b6879bbc5956b6/research/2026-10-12-spi3-clock.md),
J71s SPI ID `0x130` selects entry 48 of the captured 96-word
`clock-frequencies` table, containing 61,538,461 Hz. The same lookup for its
UART5 ID `0x118` gives 24 MHz, matching the experimental UART clock. This is
an offline candidate, not a measurement or proof of the running SPI clock;
do not enable a controller or set timing based solely on this inference.
The captured tree's SPI3 `function-spi_cs0` and touchscreen
`function-enable_cs` both reference GPIO 102, but their raw operation arguments
differ. Their electrical and pinmux semantics are unverified; equal pin
numbers do not establish that the functions are interchangeable.
As an offline feasibility check, that project's patches `0007`, `0096`, and
`0098` at revision `b94d42f78e04c5465e290340a5b6879bbc5956b6` were applied
in order to an isolated Hoolock kernel checkout at
`6831bc701a6ce059e71e5aaa9488c9195bea6927`; `drivers/spi/spi-apple.o` built
with the J71s kernel configuration and Orchard's LLVM 19 toolchain. The last
patch applied with line offsets. This initial check compiled only a driver
object and did not exercise SPI hardware or establish J71s clock,
power, pinmux, or touch compatibility. The patches are not part of this branch.
Subsequently, the full kernel image built successfully in that isolated tree
after adding the previously tested experimental battery changes. Its config
matched the J71s config; the compressed image SHA-256 is
`d244dca6b0a0d030c399321796d85ec6ad9820e0900edf9c863492b6c8984403`.
The kernel alone adds no J71s SPI device-tree node.
An incremental rebuild returned the same image digest; a separate fresh build
has not yet been compared.
The image was subsequently packaged with a controller-only J71s device tree
and booted in RAM on the test iPad. Linux bound `apple-spi` to `20a08c000.spi`
and registered `spi0` under that controller; no SPI child was present and
runtime status was suspended when checked. USB serial and the experimental
battery gauge remained available. This tested controller initialization only,
not interrupts, SPI transfers, clock accuracy, pinmux, firmware or touch.
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
