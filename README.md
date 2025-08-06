# ComfyUI-Sampler-Scheduler-Loop

A comprehensive collection of custom nodes for ComfyUI that provides automatic looping functionality through samplers, schedulers, and various parameters. Perfect for batch testing, parameter optimization, and automated workflows.

## Features

- **Automatic State Management**: No manual step increment needed - nodes handle internal counters automatically
- **Multiple Loop Modes**: Sequential, random, and ping-pong patterns
- **Parameter Range Testing**: Loop through CFG, shift, and steps values with customizable ranges
- **Sampler/Scheduler Cycling**: Test all available samplers and schedulers systematically
- **Skip Lists**: Exclude specific samplers or schedulers from loops
- **Comprehensive Combinations**: Test all parameter combinations in a single node
- **Reset Functionality**: Reset counters at any time for fresh testing cycles

## Installation

1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ComfyUI-Sampler-Scheduler-Loop.git
   ```

3. Restart ComfyUI

## Available Nodes

### 1. Float Range Loop
**Category**: `WanVideo/FloatRange`

Loop through combinations of CFG and shift float values with customizable ranges and steps.

**Inputs**:
- `cfg_start`, `cfg_end`, `cfg_step`: CFG value range parameters
- `shift_start`, `shift_end`, `shift_step`: Shift value range parameters
- `seed`: Random seed for deterministic behavior
- `reset`: Reset counter to start from beginning

**Outputs**:
- `cfg`: Current CFG value
- `shift`: Current shift value
- `current_index`: Current position in the loop
- `total_combinations`: Total number of combinations
- `current_combination`: Human-readable description of current values

### 2. Parameters Range Loop
**Category**: `WanVideo/ParametersRange`

Extended version that loops through steps, CFG, and shift values simultaneously.

**Inputs**:
- Steps range: `steps_start`, `steps_end`, `steps_interval`
- CFG range: `cfg_start`, `cfg_end`, `cfg_interval`
- Shift range: `shift_start`, `shift_end`, `shift_interval`
- `seed`: Random seed
- `reset`: Reset counter

**Outputs**:
- `steps`: Current steps value
- `cfg`: Current CFG value
- `shift`: Current shift value
- `current_index`: Current position in the loop
- `total_combinations`: Total number of combinations
- `current_combination`: Human-readable description

### 3. Sampler Loop
**Category**: `Samplers/Loop`

Automatically cycle through all available ComfyUI samplers.

**Inputs**:
- `mode`: Loop mode (`sequential`, `random`, `ping_pong`)
- `seed`: Random seed for random mode
- `reset`: Reset counter
- `skip_samplers`: Comma-separated list of samplers to skip

**Outputs**:
- `sampler`: Current sampler name
- `current_index`: Current position
- `total_combinations`: Total available samplers
- `current_combination`: Current sampler description

**Supported Loop Modes**:
- **Sequential**: Cycles through samplers in order
- **Random**: Randomly selects samplers (seeded for reproducibility)
- **Ping Pong**: Goes forward through the list, then backward

### 4. Scheduler Loop
**Category**: `Schedulers/Loop`

Similar to Sampler Loop but for schedulers.

**Inputs**:
- `mode`: Loop mode (`sequential`, `random`, `ping_pong`)
- `seed`: Random seed
- `reset`: Reset counter
- `skip_schedulers`: Comma-separated list of schedulers to skip

### 5. Sampler Scheduler Loop
**Category**: `Samplers/Loop`

Loops through combinations of samplers and schedulers.

**Inputs**:
- All inputs from individual Sampler and Scheduler loops
- `skip_samplers`: Skip specific samplers
- `skip_schedulers`: Skip specific schedulers

**Outputs**:
- `sampler`: Current sampler
- `scheduler`: Current scheduler
- `current_index`: Current combination index
- `total_combinations`: Total sampler×scheduler combinations
- `current_combination`: Description of current combination

### 6. All Parameters Loop
**Category**: `Samplers/Loop`

The ultimate comprehensive node that combines everything - loops through steps, CFG, shift, samplers, and schedulers.

**Inputs**:
- All parameter ranges (steps, CFG, shift)
- Loop mode and control options
- Skip lists for samplers and schedulers

**Outputs**:
- `steps`: Current steps value
- `cfg`: Current CFG value  
- `shift`: Current shift value
- `sampler`: Current sampler
- `scheduler`: Current scheduler
- `current_index`: Current combination index
- `total_combinations`: Total combinations possible
- `current_combination`: Full description of current settings

## Usage Examples

### Basic Parameter Testing
1. Add a `Float Range Loop` node to test different CFG and shift combinations
2. Set your desired ranges (e.g., CFG: 1.0-8.0, Shift: 1.0-3.0)
3. Connect the outputs to your KSampler node
4. Run your workflow - each execution will use the next combination

### Comprehensive Testing
1. Use `All Parameters Loop` for exhaustive testing
2. Set parameter ranges for steps (20-50), CFG (1.0-8.0), shift (1.0-3.0)
3. Optionally skip problematic samplers/schedulers using the skip lists
4. Connect all outputs to appropriate nodes in your workflow
5. Queue your workflow multiple times to cycle through all combinations

### Skip Lists Format
Enter sampler or scheduler names separated by commas:
```
euler, dpm_2, lcm
```
or
```
karras, exponential
```

## Loop Modes

- **Sequential**: Predictable order, cycles through all options systematically
- **Random**: Uses seed for reproducible randomness, good for diverse sampling  
- **Ping Pong**: Forward then backward pattern, creates smooth transitions

## Tips

- Use the `reset` input to start fresh testing cycles
- Monitor the console output for detailed logging of current selections
- The `current_combination` output is useful for file naming or logging
- Each node maintains separate counters, so you can use multiple loop nodes simultaneously

## Acknowledgments

Part of this code builds upon contributions from [tankenyuen-ola/comfyui-wanvideo-scheduler-loop](https://github.com/tankenyuen-ola/comfyui-wanvideo-scheduler-loop). Special thanks for the foundational work on parameter looping functionality.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Changelog

### v1.0.0
- Initial release with all 6 loop nodes
- Support for sequential, random, and ping-pong modes
- Automatic state management
- Skip list functionality
- Comprehensive parameter combination testing
