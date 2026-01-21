# Anvil Kernel Build Roadmap

## Global Mandates
- **Language/Format:** All implementation must be 100% **Anvil** or **MicroJSON**.
- **Exception Protocol:** Any deviation requiring a different language (e.g., C, Rust, Python) **must** be discussed with and approved by the user ("The Operator") prior to implementation.

This document tracks the sequential build orders for the next version of the Anvil Kernel.

## Build 1: [Pending/Previous]
*Context implies this was likely the base kernel or toolchain setup.*

## Build 2: Drivers (Current Focus)
**Objective:** Add all drivers needed for the current host laptop, plus a generic set for other laptops and bare-metal hypervisors.
**Status:** In Progress / Defining
**Scope:**
- **Host Specific:** Complete driver support for current hardware.
- **Generic Laptop:** Broad support for common chipsets (Wi-Fi, Graphics, Input).
- **Hypervisors:** VirtIO, VMXNET3, etc., for bare-metal virtualization support.

## Build 3: OSS Amazon Firecracker Injection
**Objective:** Inject the OSS Amazon Firecracker project into the Anvil ecosystem.
**Tech Stack:** Anvil / MicroJSON
**Status:** Planned
**Scope:**
- Ingest Firecracker source/binary.
- Adapt configuration and logging to adhere to Anvil/MicroJSON standards.

## Build 4: QEMU Testing Environment
**Objective:** Validate kernel stability and basic system functionality within QEMU.
**Status:** Planned
**Milestones:**
- **First Boot:** Successful kernel initialization and hardware detection in emulation.
- **Logon:** Functional authentication layer or initial user session entry.
- **Shell:** Operational interactive shell (Anvil Shell) for system interaction.

## Build 5: Window Manager Installation
**Objective:** Establish a graphical user interface layer.
**Status:** Planned
**Scope:**
- Selection and installation of a lightweight Window Manager (e.g., Labwc, Openbox, or Anvil-specific).
- Integration with the boot/logon flow.

## Build 6: Basic Applications
**Objective:** Provide essential system utilities for the environment.
**Status:** Planned
**Scope:**
- **Terminal:** `xterm` or the lightest available alternative.
- **Editor:** `vim` for system configuration and code editing.
- **Minimalism:** Prioritize extreme performance and low resource footprint.

## Build 7: Boot & Installation Tools
**Objective:** Finalize the distribution and installation pipeline.
**Status:** Planned
**Scope:**
- **ISO Tools:** Tooling to generate bootable ISO images (e.g., `xorriso` wrapper or Anvil-native).
- **GRUB:** Bootloader configuration and integration for both ISO and installed systems.
- **Installer:** "ISO to Disk" installer script/utility to permanently install the OS from live media.

## Build 8: Zero-Username 2FA Logon
**Objective:** Implement a high-security, identity-agnostic authentication flow.
**Status:** Planned
**Scope:**
- **No Username:** Remove reliance on traditional user strings; identity is derived or implicit.
- **2FA Only:** Authentication relies solely on Time-based One-Time Passwords (TOTP).
- **Compatibility:** Ensure codes are generatable by standard apps like Bitwarden or Authy.

## Build 9: Microkernel Apps & Extended Software
**Objective:** Decouple all non-core functionality into microkernel-style services and provide a complete agent/developer toolset.
**Status:** Planned
**Scope:**
- **Core Anvil:** Cortex, aimeat, and other autonomous agents.
- **Development:** Anvil Compiler, Git, GitHub CLI (gh), RFC documentation suite.
- **Productivity:** Chromium, Email, Rich Terminal, Rich Text Editor, VS Code.
- **Cloud & Infrastructure:** GCloud SDK, AWS SDK, Azure SDK, Google Drive Connector.
- **Mainframe Suite:** Emulators, Compilers, and Tape Library support.
- **System Utilities:** CLI-style File Manager, `btop`.
- **Modularity:** All software listed above to be treated as modular microkernel services.
