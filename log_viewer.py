import os
import json
import argparse


def format_log_entry(line):
    """Format log entry for better readability"""
    try:
        if '{' in line and '}' in line:
            parts = line.split(' | ')
            if len(parts) >= 4:
                timestamp = parts[0]
                level = parts[1]
                module = parts[2]
                
                json_start = line.find('{')
                if json_start != -1:
                    json_data = json.loads(line[json_start:])
                    
                    if 'command' in json_data:
                        return f"[{timestamp}] {level} - Command '{json_data['command']}' by {json_data['user']} in {json_data['guild']}"
                    elif 'action' in json_data:
                        song_title = json_data.get('song', {}).get('title', 'Unknown')
                        return f"[{timestamp}] {level} - Music: {json_data['action']} - {song_title} by {json_data['user']}"
                    elif 'event_type' in json_data:
                        return f"[{timestamp}] {level} - {json_data['event_type']}: {json_data.get('details', '')}"
        
        return line.strip()
    except:
        return line.strip()


def tail_file(filename, lines=50):
    """Read last N lines from file"""
    try:
        with open(filename, 'r') as f:
            return f.readlines()[-lines:]
    except FileNotFoundError:
        print(f"Log file {filename} not found!")
        return []
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []


def watch_file(filename):
    """Watch file for new entries (simple implementation)"""
    try:
        print(f"Watching {filename} for new entries... (Ctrl+C to stop)")
        
        if not os.path.exists(filename):
            print(f"File {filename} doesn't exist yet. Waiting...")
            return
            
        with open(filename, 'r') as f:
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(format_log_entry(line), flush=True)
                else:
                    import time
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\nStopped watching.")
    except Exception as e:
        print(f"Error watching file: {e}")


def show_stats():
    """Show log statistics"""
    log_files = {
        'bot.log': 'Main Bot Log',
        'music.log': 'Music Activity',
        'errors.log': 'Error Log'
    }
    
    print("📊 Log Statistics:")
    print("-" * 50)
    
    for filename, description in log_files.items():
        filepath = f"logs/{filename}"
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    size = os.path.getsize(filepath)
                    
                print(f"{description:.<20} {len(lines):>6} lines ({size/1024:.1f} KB)")
            except Exception as e:
                print(f"{description:.<20} Error: {e}")
        else:
            print(f"{description:.<20} Not found")


def main():
    parser = argparse.ArgumentParser(description='Discord Bot Log Viewer')
    parser.add_argument('log_type', nargs='?', default='bot', 
                       choices=['bot', 'music', 'errors', 'all'],
                       help='Type of log to view (default: bot)')
    parser.add_argument('-n', '--lines', type=int, default=50,
                       help='Number of lines to show (default: 50)')
    parser.add_argument('-w', '--watch', action='store_true',
                       help='Watch for new log entries')
    parser.add_argument('-s', '--stats', action='store_true',
                       help='Show log statistics')
    
    args = parser.parse_args()
    
    if args.stats:
        show_stats()
        return
    
    if not os.path.exists('logs'):
        print("Logs directory doesn't exist. Run the bot first to generate logs.")
        return
    
    log_files = {
        'bot': 'logs/bot.log',
        'music': 'logs/music.log', 
        'errors': 'logs/errors.log'
    }
    
    if args.log_type == 'all':
        print("📋 All Recent Log Entries:")
        print("=" * 60)
        for log_type, filename in log_files.items():
            if os.path.exists(filename):
                print(f"\n--- {log_type.upper()} LOG ---")
                lines = tail_file(filename, args.lines // len(log_files))
                for line in lines:
                    print(format_log_entry(line))
    else:
        filename = log_files.get(args.log_type)
        if not filename or not os.path.exists(filename):
            print(f"Log file for '{args.log_type}' not found!")
            return
        
        if args.watch:
            watch_file(filename)
        else:
            print(f"📋 Last {args.lines} entries from {args.log_type} log:")
            print("=" * 60)
            lines = tail_file(filename, args.lines)
            for line in lines:
                print(format_log_entry(line))


if __name__ == '__main__':
    main() 