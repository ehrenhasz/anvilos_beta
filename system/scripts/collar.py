import os
import sys
import re

class Collar:
    """
    RFC-030/RFC-028: The Collar
    Enforces the prohibition of unauthorized entropy sources.
    """
    
    BANNED_PATTERNS = [
        (r"import\s+random", "Standard 'random' library is BANNED. Use Hydrogen."),
        (r"from\s+random\s+import", "Standard 'random' library is BANNED. Use Hydrogen."),
        (r"/dev/urandom", "Direct access to /dev/urandom is BANNED. Use Hydrogen."),
        (r"~/\.gemini", "Usage of ~/.gemini is BANNED. Use /mnt/anvil_temp.")
    ]

    IGNORE_DIRS = [
        ".git", "node_modules", "dist", "build", "__pycache__"
    ]
    
    IGNORE_FILES = [
        "collar.py", "hydrogen.ts", "package-lock.json", "warden.py" # Self-reference allowed for policing
    ]

    def scan_file(self, filepath):
        violations = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern, message in self.BANNED_PATTERNS:
                    if re.search(pattern, content):
                        violations.append(message)
        except Exception as e:
            print(f"[COLLAR] Warning: Could not scan {filepath}: {e}")
        return violations

    def stage_files(self, root_dir):
        print(f"[COLLAR] Staging files in {root_dir}...")
        staged_count = 0
        skipped_count = 0
        
        # Extensions to ignore (build garbage)
        IGNORE_EXTS = {'.o', '.obj', '.pyc', '.class', '.dll', '.exe', '.so', '.a', '.lib', '.iso', '.img', '.tar.gz', '.zip', '.swp'}
        
        # Large file threshold (10 MB)
        LARGE_FILE_LIMIT = 10 * 1024 * 1024 

        for root, dirs, files in os.walk(root_dir):
            # Filter directories in place
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS and d not in ['tmp', 'temp', 'logs', 'artifacts', 'build', 'dist']]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                # Check extension
                _, ext = os.path.splitext(file)
                if ext.lower() in IGNORE_EXTS:
                    # print(f"Skipping garbage: {filepath}")
                    skipped_count += 1
                    continue
                
                # Check size
                try:
                    size = os.path.getsize(filepath)
                    if size > LARGE_FILE_LIMIT:
                        print(f"[SKIP] Large file ({size/1024/1024:.2f}MB): {filepath}")
                        skipped_count += 1
                        continue
                except OSError:
                    continue

                # Stage file
                try:
                    subprocess.run(["git", "add", filepath], check=True, capture_output=True)
                    # print(f"Staged: {filepath}")
                    staged_count += 1
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Failed to stage {filepath}: {e}")

        print(f"[COLLAR] Staging complete. Staged: {staged_count}, Skipped: {skipped_count}")

    def scan_directory(self, root_dir, mode="cli"):
        if mode == "cli":
            print(f"[COLLAR] Scanning {root_dir} for entropy violations...")
        has_violations = False
        violations_data = []
        
        for root, dirs, files in os.walk(root_dir):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                if file in self.IGNORE_FILES:
                    continue
                
                # Only scan code files
                if not file.endswith(('.py', '.js', '.ts', '.tsx', '.sh')):
                    continue
                    
                filepath = os.path.join(root, file)
                violations = self.scan_file(filepath)
                
                if violations:
                    has_violations = True
                    violations_data.append({"path": filepath, "issues": violations})
                    if mode == "cli":
                        print(f"\n[VIOLATION] File: {filepath}")
                        for v in violations:
                            print(f"  -> {v}")

        if has_violations:
            if mode == "gui":
                print(f"GUI_MODE: FOUND {len(violations_data)} VIOLATIONS")
                # Future: Launch GUI window here
            elif mode == "cli":
                print("\n[COLLAR] VIOLATIONS DETECTED. ROLLBACK REQUIRED.")
            sys.exit(1)
        else:
            if mode == "gui":
                print("GUI_MODE: CLEAN")
            elif mode == "cli":
                print("\n[COLLAR] Clean. No unauthorized entropy sources detected.")
            sys.exit(0)

if __name__ == "__main__":
    import argparse
    import subprocess
    
    parser = argparse.ArgumentParser(description="Collar Entropy Scanner & Git Warden")
    parser.add_argument("command", nargs="?", default="stage", choices=["scan", "stage"], help="Action to perform: 'stage' (default) or 'scan'")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to process")
    parser.add_argument("--go", choices=["cli", "gui"], default="cli", help="Execution mode (for scan)")
    
    args = parser.parse_args()
    
    collar = Collar()
    
    if args.command == "scan":
        collar.scan_directory(args.root, mode=args.go)
    elif args.command == "stage":
        collar.stage_files(args.root)
