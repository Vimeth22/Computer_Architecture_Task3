import argparse
import random
from collections import OrderedDict

ORDER = ["SSD", "DRAM", "L3", "L2", "L1"]


def hx(v: int) -> str:
    return f"0x{v:08X}"


def is_adjacent(src: str, dst: str) -> bool:
    return src in ORDER and dst in ORDER and abs(ORDER.index(src) - ORDER.index(dst)) == 1


class Level:
    def __init__(self, name: str, size: int, policy: str = "FIFO"):
        self.name, self.size, self.policy = name, size, policy.upper()
        self.data, self.lru = [], OrderedDict()

    def has(self, ins: int) -> bool:
        ok = ins in self.data
        if ok and self.policy == "LRU":
            self.lru[ins] = None
            self.lru.move_to_end(ins)
        return ok

    def add(self, ins: int):
        if ins in self.data:
            if self.policy == "LRU":
                self.lru[ins] = None
                self.lru.move_to_end(ins)
            return None, "already_present"
        evicted = None
        if len(self.data) >= self.size:
            if self.policy == "RANDOM":
                evicted = self.data.pop(random.randrange(len(self.data)))
            elif self.policy == "LRU":
                evicted = next(iter(self.lru))
                self.lru.pop(evicted)
                self.data.remove(evicted)
            else:
                evicted = self.data.pop(0)
        self.data.append(ins)
        if self.policy == "LRU":
            self.lru[ins] = None
        return evicted, "added"

    def snapshot(self):
        return [hx(x) for x in self.data]


class MemoryHierarchySimulator:
    def __init__(self, sizes, latencies, bandwidth=1, replacement_policy="FIFO"):
        self._validate_sizes(sizes)
        self._validate_latencies(latencies)
        if bandwidth < 1:
            raise ValueError("bandwidth must be >= 1")
        self.clock, self.bandwidth, self.lat = 0, bandwidth, latencies
        self.trace, self.moves = [], []
        self.stats = {k: {"hits": 0, "misses": 0} for k in ["L1", "L2", "L3", "DRAM", "SSD"]}
        self.levels = {
            "SSD": Level("SSD", sizes["SSD"], replacement_policy),
            "DRAM": Level("DRAM", sizes["DRAM"], replacement_policy),
            "L3": Level("L3", sizes["L3"], replacement_policy),
            "L2": Level("L2", sizes["L2"], replacement_policy),
            "L1": Level("L1", sizes["L1"], replacement_policy),
        }

    @staticmethod
    def _validate_sizes(s):
        keys = ["SSD", "DRAM", "L3", "L2", "L1"]
        if any(k not in s for k in keys):
            raise ValueError("sizes must include SSD, DRAM, L3, L2, L1")
        if any(s[k] <= 0 for k in keys):
            raise ValueError("all sizes must be positive")
        if not (s["SSD"] > s["DRAM"] > s["L3"] > s["L2"] > s["L1"]):
            raise ValueError("Hierarchy rule violated: SSD > DRAM > L3 > L2 > L1")

    @staticmethod
    def _validate_latencies(lat):
        for (src, dst), cyc in lat.items():
            if not is_adjacent(src, dst):
                raise ValueError(f"latency for non-adjacent levels: {src}->{dst}")
            if cyc < 1:
                raise ValueError("latency must be >= 1")

    @staticmethod
    def _validate_instruction(ins):
        if not isinstance(ins, int):
            raise TypeError("instruction must be int")
        if not (0 <= ins <= 0xFFFFFFFF):
            raise ValueError("instruction must be 32-bit unsigned")

    def _tick(self, cycles, reason):
        for _ in range(cycles):
            self.clock += 1
            self.moves.append(f"[cycle {self.clock:04d}] {reason}")

    def load_ssd(self, instructions):
        ssd = self.levels["SSD"]
        for ins in instructions:
            self._validate_instruction(ins)
            if ins in ssd.data:
                continue
            if len(ssd.data) >= ssd.size:
                raise ValueError("SSD capacity exceeded")
            ssd.data.append(ins)

    def _transfer(self, src, dst, instructions, tag):
        if not is_adjacent(src, dst):
            raise ValueError(f"Bypass not allowed: {src}->{dst}")
        src_level, dst_level, latency = self.levels[src], self.levels[dst], self.lat.get((src, dst), 1)
        for i in range(0, len(instructions), self.bandwidth):
            chunk = instructions[i : i + self.bandwidth]
            self._tick(latency, f"{tag} waiting ({src}->{dst})")
            for ins in chunk:
                if ins not in src_level.data:
                    raise ValueError(f"{hx(ins)} not present in {src}")
                ev, state = dst_level.add(ins)
                msg = f"[cycle {self.clock:04d}] {tag}: {hx(ins)} {src}->{dst}"
                if state == "already_present":
                    msg += " (already present)"
                elif ev is not None:
                    msg += f" | evicted from {dst}: {hx(ev)}"
                self.moves.append(msg)

    def read(self, ins):
        self._validate_instruction(ins)
        self.trace.append(f"READ request {hx(ins)}")
        if self.levels["L1"].has(ins):
            self.stats["L1"]["hits"] += 1
            self.trace.append(f"READ hit at L1 for {hx(ins)}")
            return ins
        self.stats["L1"]["misses"] += 1
        found = None
        for lv in ["L2", "L3", "DRAM", "SSD"]:
            if self.levels[lv].has(ins):
                self.stats[lv]["hits"] += 1
                self.trace.append(f"READ found at {lv} for {hx(ins)}")
                found = lv
                break
            self.stats[lv]["misses"] += 1
        if not found:
            raise ValueError(f"instruction not found: {hx(ins)}")
        path, idx = ["SSD", "DRAM", "L3", "L2", "L1"], ["SSD", "DRAM", "L3", "L2", "L1"].index(found)
        for j in range(idx, len(path) - 1):
            self._transfer(path[j], path[j + 1], [ins], "READ_FILL")
        self.trace.append(f"READ complete at CPU for {hx(ins)}")
        return ins

    def write(self, ins):
        self._validate_instruction(ins)
        self.trace.append(f"WRITE request {hx(ins)}")
        if not self.levels["L1"].has(ins):
            self.trace.append(f"WRITE prefetch needed for {hx(ins)}")
            self.read(ins)
        for src, dst in [("L1", "L2"), ("L2", "L3"), ("L3", "DRAM"), ("DRAM", "SSD")]:
            self._transfer(src, dst, [ins], "WRITE_BACK")
        self.trace.append(f"WRITE complete down to SSD for {hx(ins)}")

    def run_workload(self, ops):
        for op, ins in ops:
            if op.upper() == "READ":
                self.read(ins)
            elif op.upper() == "WRITE":
                self.write(ins)
            else:
                raise ValueError(f"unknown op: {op}")

    def report(self):
        out = ["Memory Hierarchy Configuration"]
        for lv in ORDER:
            out.append(f"{lv}: size={self.levels[lv].size} instructions")
        out.append(f"Clock cycles elapsed: {self.clock}")
        out.append(f"Bandwidth (instructions/transfer): {self.bandwidth}")
        out.append("Latencies (cycles per adjacent transfer):")
        for src, dst in [("SSD", "DRAM"), ("DRAM", "L3"), ("L3", "L2"), ("L2", "L1")]:
            out.append(f"  {src}->{dst}: {self.lat[(src, dst)]}")
        out.append("\n Instruction Access Trace")
        out.extend(self.trace or ["<no accesses>"])
        out.append("\n Data Movement Across Levels")
        out.extend(self.moves or ["<no movement>"])
        out.append("\n Cache/Memory Hits and Misses")
        for lv in ["L1", "L2", "L3", "DRAM", "SSD"]:
            st = self.stats[lv]
            out.append(f"{lv}: hits={st['hits']}, misses={st['misses']}")
        out.append("\n Final State of Memory Levels")
        for lv in ORDER:
            out.append(f"{lv}: {self.levels[lv].snapshot()}")
        return "\n".join(out)


def build_latencies(ssd_dram, dram_l3, l3_l2, l2_l1):
    return {
        ("SSD", "DRAM"): ssd_dram,
        ("DRAM", "SSD"): ssd_dram,
        ("DRAM", "L3"): dram_l3,
        ("L3", "DRAM"): dram_l3,
        ("L3", "L2"): l3_l2,
        ("L2", "L3"): l3_l2,
        ("L2", "L1"): l2_l1,
        ("L1", "L2"): l2_l1,
    }


def parse_args():
    p = argparse.ArgumentParser(description="Task3 Memory Hierarchy: SSD -> DRAM -> L3 -> L2 -> L1 -> CPU")
    p.add_argument("--ssd", type=int, default=64)
    p.add_argument("--dram", type=int, default=32)
    p.add_argument("--l3", type=int, default=16)
    p.add_argument("--l2", type=int, default=8)
    p.add_argument("--l1", type=int, default=4)
    p.add_argument("--bandwidth", type=int, default=1)
    p.add_argument("--replacement", choices=["FIFO", "LRU", "RANDOM"], default="FIFO")
    p.add_argument("--lat-ssd-dram", type=int, default=5)
    p.add_argument("--lat-dram-l3", type=int, default=4)
    p.add_argument("--lat-l3-l2", type=int, default=2)
    p.add_argument("--lat-l2-l1", type=int, default=1)
    return p.parse_args()


def main():
    a = parse_args()
    sim = MemoryHierarchySimulator(
        sizes={"SSD": a.ssd, "DRAM": a.dram, "L3": a.l3, "L2": a.l2, "L1": a.l1},
        latencies=build_latencies(a.lat_ssd_dram, a.lat_dram_l3, a.lat_l3_l2, a.lat_l2_l1),
        bandwidth=a.bandwidth,
        replacement_policy=a.replacement,
    )
    sim.load_ssd([0x1000 + i for i in range(20)])
    sim.run_workload([
        ("READ", 0x1001), ("READ", 0x1002), ("READ", 0x1003), ("READ", 0x1001),
        ("READ", 0x1004), ("READ", 0x1005), ("WRITE", 0x1002), ("READ", 0x1008),
        ("WRITE", 0x1008), ("READ", 0x1003),
    ])
    print(sim.report())


if __name__ == "__main__":
    main()
