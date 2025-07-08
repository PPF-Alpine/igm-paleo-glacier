#!/bin/bash

# estimate_sim_time.sh - Estimates remaining time for IGM simulations
# Usage: ./estimate_sim_time.sh <log_file> [final_year]

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <log_file> [final_year]"
    echo "Example: $0 simulation.log 1950"
    exit 1
fi

LOG_FILE="$1"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Error: Log file '$LOG_FILE' not found."
    exit 1
fi

# Set final year (default is 1950, can be overridden with second argument)
FINAL_YEAR=1950
if [ $# -ge 2 ]; then
    FINAL_YEAR=$2
fi

# Extract the time stamps and simulation years
echo "Analyzing simulation log file: $LOG_FILE"
echo "Target year: $FINAL_YEAR"
echo ""

# Get the last line with simulation data (excluding GPU metric lines)
LAST_LINE=$(grep "IGM [0-9:]" "$LOG_FILE" | tail -n 1)

if [ -z "$LAST_LINE" ]; then
    echo "Error: No simulation data found in log file."
    exit 1
fi

# Extract current simulation year (handling negative years)
CURRENT_YEAR=$(echo "$LAST_LINE" | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2}')
if [ -z "$CURRENT_YEAR" ]; then
    echo "Error: Could not extract current simulation year."
    exit 1
fi

# Remove any non-numeric characters except minus sign
CLEANED_YEAR=$(echo "$CURRENT_YEAR" | sed 's/[^0-9-]//g')

# Convert to numeric value
NUMERIC_YEAR=$CLEANED_YEAR
# Convert to positive value for calculations if it's negative
if [[ $NUMERIC_YEAR == -* ]]; then
    # Remove minus sign for calculations
    POSITIVE_YEAR=${NUMERIC_YEAR#-}
else
    POSITIVE_YEAR=$NUMERIC_YEAR
fi

# Extract last timestamp
LAST_TIMESTAMP=$(echo "$LAST_LINE" | awk '{print $2, $3}')

echo "Current progress:"
echo "- Current simulation year: $NUMERIC_YEAR"
echo "- Last update: $LAST_TIMESTAMP"

# Calculate years remaining (adjusted for negative years)
if [[ $NUMERIC_YEAR == -* ]]; then
    # For negative years, we need to add the absolute values
    YEARS_REMAINING=$((FINAL_YEAR + POSITIVE_YEAR))
else
    YEARS_REMAINING=$((FINAL_YEAR - NUMERIC_YEAR))
fi

if [ $YEARS_REMAINING -le 0 ]; then
    echo "Simulation has reached or passed the target year of $FINAL_YEAR."
    exit 0
fi

echo "- Years remaining: $YEARS_REMAINING"

# Get last 10 time intervals to calculate average progression rate
LINES=$(grep "IGM [0-9:]" "$LOG_FILE" | tail -n 10)
LINES_COUNT=$(echo "$LINES" | wc -l)

if [ $LINES_COUNT -lt 2 ]; then
    echo "Not enough data points to estimate completion time."
    exit 1
fi

# Calculate time differences and year differences for estimation
PREV_TIMESTAMP=""
PREV_YEAR=""
TOTAL_HOURS=0
TOTAL_YEARS=0
COUNT=0


while IFS= read -r line; do
    # Extract timestamp (convert to seconds since midnight)
    TIMESTAMP=$(echo "$line" | awk '{print $2, $3}')
    TIMESTAMP=${TIMESTAMP::-2}
    TIMESTAMP_SECONDS=$(date -d "$TIMESTAMP" +%s 2>/dev/null) 

    # Skip invalid timestamps
    if [ $? -ne 0 ]; then
        continue
    fi
    
    # Extract year
    YEAR=$(echo "$line" | awk -F'|' '{print $2}' | tr -d '[:space:]')

    
    if [ -n "$PREV_TIMESTAMP" ] && [ -n "$PREV_YEAR" ]; then
        # Calculate time difference in hours
        TIME_DIFF_SECONDS=$((TIMESTAMP_SECONDS - PREV_TIMESTAMP_SECONDS))
        TIME_DIFF_HOURS=$(echo "scale=2; $TIME_DIFF_SECONDS / 3600" | bc)
        
        # Calculate year difference (handle negative years)
        if [[ $YEAR == -* ]] && [[ $PREV_YEAR == -* ]]; then
            # Both are negative, we need the difference of absolute values
            YEAR_ABS=${YEAR#-}
            PREV_YEAR_ABS=${PREV_YEAR#-}
            # Progress is from more negative to less negative (decreasing absolute value)
            YEAR_DIFF=$(echo "$PREV_YEAR_ABS - $YEAR_ABS" | bc)
        else
            # Simple case
            YEAR_DIFF=$(echo "$YEAR - $PREV_YEAR" | bc)
        fi
        
        if [ $(echo "$YEAR_DIFF > 0" | bc) -eq 1 ]; then  # Only consider positive progression
            TOTAL_HOURS=$(echo "$TOTAL_HOURS + $TIME_DIFF_HOURS" | bc)
            TOTAL_YEARS=$(echo "$TOTAL_YEARS + $YEAR_DIFF" | bc)
            COUNT=$((COUNT + 1))
        fi
    fi
    
    PREV_TIMESTAMP=$TIMESTAMP
    PREV_TIMESTAMP_SECONDS=$TIMESTAMP_SECONDS
    PREV_YEAR=$YEAR
    
done <<< "$LINES"

if [ $COUNT -eq 0 ] || [ $(echo "$TOTAL_YEARS == 0" | bc) -eq 1 ]; then
    echo "Not enough valid data points to estimate completion time."
    exit 1
fi

TIMESTEP=$(echo "$YEAR_DIFF")

# Calculate rate in hours per simulation year
RATE=$(echo "scale=4; $TOTAL_HOURS / $TOTAL_YEARS" | bc)
RATE_MIN=$(echo "$RATE * 60" | bc)
RATE_PER_TIMESTEP=$(echo "$RATE * $TIMESTEP"| bc)
RATE_PER_TIMESTEP_MIN=$(echo "$RATE_PER_TIMESTEP * 60" | bc)

# Estimate remaining time
REMAINING_HOURS=$(echo "scale=2; $RATE * $YEARS_REMAINING" | bc)
REMAINING_DAYS=$(echo "scale=2; $REMAINING_HOURS / 24" | bc)

# Calculate estimated completion date and time
CURRENT_TIME=$(date +%s)
SECONDS_TO_COMPLETE=$(echo "$REMAINING_HOURS * 3600" | bc | cut -d. -f1)
COMPLETION_TIME=$((CURRENT_TIME + SECONDS_TO_COMPLETE))
COMPLETION_DATE=$(date -d "@$COMPLETION_TIME" "+%Y-%m-%d %H:%M:%S")

echo ""
echo "Estimation based on recent progression:"
echo "- Average time per simulation year: $RATE hours, ($RATE_MIN minutes)"
echo "- Average time per simulation step: $RATE_PER_TIMESTEP, hours ($RATE_PER_TIMESTEP_MIN, minutes)"
echo "- Estimated remaining time: $REMAINING_HOURS hours ($REMAINING_DAYS days)"
echo "- Estimated completion date: $COMPLETION_DATE"

# Find starting year to calculate progress
FIRST_LINE=$(grep "IGM [0-9:]" "$LOG_FILE" | head -n 1)
START_YEAR=$(echo "$FIRST_LINE" | awk -F'|' '{print $2}' | tr -d '[:space:]')

# Calculate progress percentage
if [[ $START_YEAR == -* ]] && [[ $NUMERIC_YEAR == -* ]]; then
    # Both are negative
    START_ABS=${START_YEAR#-}
    CURRENT_ABS=${NUMERIC_YEAR#-}
    TOTAL_SPAN=$(echo "$START_ABS - ($FINAL_YEAR * -1)" | bc)
    COMPLETED=$(echo "$START_ABS - $CURRENT_ABS" | bc)
else
    # Handle other cases
    TOTAL_SPAN=$(echo "$FINAL_YEAR - $START_YEAR" | bc)
    COMPLETED=$(echo "$NUMERIC_YEAR - $START_YEAR" | bc)
fi

PROGRESS_PERCENT=$(echo "scale=2; 100 * $COMPLETED / $TOTAL_SPAN" | bc)

echo "- Current progress: $PROGRESS_PERCENT% complete"
