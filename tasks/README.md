# Z Task Management

This package adds task management functionality to the Z application.

## Features

- **Task Toggle Button**: Mark entries as tasks with a single click
- **Task Column in CSV**: All data is stored in Z.csv with a new "task" column
- **Task Extraction Tool**: Extract tasks to a separate CSV file

## Installation

1. Ensure the `tasks` directory is in your Z application root directory
2. The task manager will be automatically loaded when you start Z

## Usage

### Marking Tasks

1. Type your text in the input field
2. Click the "Task: Off" button (it will mark the entry as a task)
3. The text will be saved with task=1 in Z.csv

### Extracting Tasks

To extract tasks to a separate CSV file:

```
python -m tasks.extract_tasks
```

This will:
1. Open a GUI to select input and output files
2. Extract all entries with task=1 from the input file
3. Save them to the output file

You can also run it from the command line:

```
python -m tasks.extract_tasks [input_file] [output_file]
```

## File Structure

```
tasks/
├── __init__.py        # Package initialization
├── task_manager.py    # Task management functionality
├── extract_tasks.py   # Task extraction tool
└── README.md          # This documentation file
```

## Extending This Functionality

This is just the first step toward a more comprehensive data management system:

1. **Custom Columns**: More columns can be added to Z.csv for different types of metadata
2. **Filtering Options**: Extract entries based on multiple criteria
3. **Data Visualization**: Create visualizations based on task data
4. **Advanced Queries**: Search and filter tasks based on complex conditions

## Notes

- If your Z.csv file was created before adding this module, the task column will be added automatically
- All existing entries will have task=0 by default
- The task button always resets to "Task: Off" after each entry