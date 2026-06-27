#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch Frontend
osascript -e "tell application \"Terminal\" to do script \"cd '$DIR' && ./frontend.sh\""

# Close this initial launcher window
osascript -e 'tell application "Terminal" to close (every window whose name contains "launch_nemesis")' & exit

