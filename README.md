# Task 3

## Memory Hierarchy Simulation (SSD → DRAM → L3 → L2 → L1 → CPU)

---

## 1) Project Objective

Model instruction movement through a strict memory hierarchy:

`SSD -> DRAM -> L3 -> L2 -> L1 -> CPU`

The simulator enforces:
- No bypassing of intermediate levels
- 32-bit instruction values
- Configurable hierarchy sizes
- Configurable transfer latency and bandwidth
- Read and write-back behavior

---

## 2) Implemented Features

### Core Requirements
- `SSD`, `DRAM`, `L3`, `L2`, `L1` memory levels
- Strict hierarchy order validation: `SSD > DRAM > L3 > L2 > L1`
- Clock-cycle simulation for every transfer
- Multi-cycle transfer latency support
- Optional bandwidth limit (instructions transferred per cycle)
- Read operation (`READ`) from hierarchy to CPU
- Write-back operation (`WRITE`) from `L1` down to `SSD`
- Final reporting of memory states and statistics

### Cache Full Behavior (Section 5)
- Eviction occurs when cache level is full
- Bonus replacement policies implemented:
  - `FIFO`
  - `LRU`
  - `RANDOM`

---

## 3) File Structure

- `Task3.py` 
- `README.md`
---

## 4) Requirements

- Python 3.10+ (recommended)
- No external third-party packages required

---

## 5) How to Run

From the project folder:

```bash
python Task3.py
```

---

## 6) Command-Line Options

You can customize memory sizes, latency, bandwidth, and replacement policy.

```bash
python Task3.py \
  --ssd 64 \
  --dram 32 \
  --l3 16 \
  --l2 8 \
  --l1 4 \
  --bandwidth 1 \
  --replacement FIFO \
  --lat-ssd-dram 5 \
  --lat-dram-l3 4 \
  --lat-l3-l2 2 \
  --lat-l2-l1 1
```

### Parameters
- `--ssd`, `--dram`, `--l3`, `--l2`, `--l1`: capacities in number of instructions
- `--bandwidth`: max instructions per transfer batch (per latency interval)
- `--replacement`: `FIFO`, `LRU`, or `RANDOM`
- `--lat-ssd-dram`, `--lat-dram-l3`, `--lat-l3-l2`, `--lat-l2-l1`: transfer latency in cycles

---

## 7) Output Sections

The program prints:
1. Memory hierarchy configuration
2. Instruction access trace
3. Data movement log across levels
4. Cache/memory hits and misses
5. Final state of each memory level

---

## 8) Assignment Requirement Coverage

- Section 1 (Memory System Design): Implemented
- Section 2 (Parameterization): Implemented
- Section 3 (Clock + Data Movement): Implemented
- Section 4 (Read/Write Operations): Implemented
- Section 5 (Cache Behavior): Implemented (+ bonus policies)
- Section 6 (No Bypass Rules): Implemented
- Program Output requirements: Implemented

---

## 9) Notes for Submission

For full assignment submission, include:
- `Task3.py`
- This `README.md`
- GitHub Link: https://github.com/Vimeth22/Computer_Architecture_Task3
- Demo Video Link: https://drive.google.com/file/d/1ipfWGOqBdCIST_Ek_Re5LD0urbNkvhq6/view?usp=sharing
- Response to: “Can video recordings be uploaded to YouTube?” -> **Yes**
