"""
Main entry point untuk Face Recognition System
"""
import sys
import argparse

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Face Recognition System")
    parser.add_argument(
        'mode',
        choices=['batch', 'api', 'web'],
        help='Mode: batch (batch encoding), api (REST API), web (web interface)'
    )
    parser.add_argument(
        '--sample', type=int, help='Process N random samples (batch mode)'
    )
    parser.add_argument(
        '--files', nargs='+', help='Process custom files (batch mode)'
    )
    parser.add_argument(
        '--all', action='store_true', help='Process all files (batch mode)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'batch':
        from face_recognition.batch_encoder import main as batch_main
        # Pass arguments to batch encoder
        sys.argv = ['batch_encoder.py']
        if args.files:
            sys.argv.extend(['--files'] + args.files)
        elif args.sample:
            sys.argv.extend(['--sample', str(args.sample)])
        elif args.all:
            sys.argv.append('--all')
        batch_main()
    elif args.mode == 'api':
        from api.recognition_api import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    elif args.mode == 'web':
        from api.web_interface import app
        app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()

