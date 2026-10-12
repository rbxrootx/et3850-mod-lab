# We gave an Epson ET-3850 a root shell—and made its Wi-Fi driver stay awake

*An owner-led firmware experiment, a real printer, and a crucial distinction between “we signed it” and “it booted.”*

I started with a simple complaint: the Wi-Fi on my ET-3850 was unreliable. The goal grew into a bigger question. Could I change the printer's firmware myself, get a shell, and eventually make the screen look like mine?

After unpacking images, tracing update traffic, and testing against the physical printer, we have an answer to part of that question: **a custom modification is running on this ET-3850**. We verified a password-gated root shell, a changed network executable, and live Wi-Fi driver parameters. Long-term network stability, a real photo wallpaper, and SSH remain open work.

## What is inside the printer?

The ET-3850 already runs Linux. The image we inspected contains a Linux 4.4.27 ARMv7 environment, compressed SquashFS filesystems, Epson's network program, and a Realtek 8723DU Wi-Fi driver. We did not need to replace the entire operating system for the first experiment. A focused change to the existing system gave us a way to test whether custom code actually ran.

The firmware package has multiple records with ordinary integrity fields such as sums and hashes. It also carries an ECDSA P-256 signature. Those are different protections. We could recompute the ordinary record fields after editing bytes. We could **not** generate a valid Epson signature: that would require Epson's private signing key.

So how did a modified image install? We found an update-path acceptance issue while analyzing the controller and tested a candidate against the printer. Our modified package still failed normal signature verification in an offline checker. On the physical device, the new startup behavior appeared and the modified binary matched our build. That establishes installation, although it does not prove every step of the controller's internal decision sequence. The reproducible bypass and installer remain outside this public repository while we prepare a vendor report.

## Proof beyond an “OK” response

An update transport saying “OK” was not enough. We added an unmistakable hostname marker, ET3850MOD, to a startup script. After the printer restarted, that marker appeared in a live login prompt. It was direct evidence of our startup code running on the device.

The original Telnet login on port 23 did not accept our generated password. We did not discover or crack Epson's root password. Instead, the modified filesystem starts a **new** password-gated launcher on port 2323. We generated a private password for it; the image carries only a digest for checking that password. We then asked the live printer for its identity:

> uid=0(root) gid=0(root)

A second read-only check returned Linux 4.4.27 on ARMv7. The running network executable's digest matched our patched file. The Realtek driver reported both power-related settings at zero:

> rtw_power_mgnt = 0  
> rtw_enusbss = 0

The printer was reachable over Wi-Fi immediately after the modified boot. One JPEG cake-page print sent through IPPS reached the printer's completed job state. That is a useful smoke test, not evidence that the original disconnect problem is solved. We still need days of ordinary use to measure that.

## What root lets us do now

We can inspect the running Linux system, examine processes and logs, measure network behavior, and make controlled changes through the custom shell. A keyed SSH service is a sensible next improvement. The custom service currently uses Telnet, whose traffic is plaintext on the local network. We have not found stock SSH listening or installed an SSH daemon yet.

The LCD is another challenge. We found 320×240 image assets in the controller firmware and built a local version of an owner's photo into one image slot. But the visible home screen is white with blue tiles, and the printer's wallpaper menu offers only solid colors. We have not identified the renderer path that would put the photo on that actual home screen. That feature is still unverified.

Root access also does not turn the printer into a general-purpose PC. The ET-3850 already runs Linux, but replacing it with another distribution would require boot support and working drivers for the display, print engine, scanner, and Epson controller.

## What is public

This repository contains the confirmed observations and a small Python companion client for printers **already modified by their owners**. The client can check whether the custom shell is reachable and connect using an owner's own password file. It does not install firmware. There is no Epson firmware binary, password, personal photo, or reproducible update bypass here.

The most interesting result is not that a transfer finished. It is that the physical printer booted altered startup code, displayed our login marker, returned a root identity, and loaded the Wi-Fi driver with our chosen settings. Now we can test whether those settings make Wi-Fi better in daily use—and keep working toward a photo on that stubborn white home screen.
