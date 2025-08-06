"""
ComfyUI-Sampler-Scheduler-Loop
A custom node for looping through samplers and schedulers in ComfyUI
"""

import random
import sys
import os

# Try to import ComfyUI sampler names
try:
    from comfy.samplers import KSAMPLER_NAMES
    print(f"ComfyUI sampler names loaded successfully: {len(KSAMPLER_NAMES)} samplers")
    print(f"First few samplers: {KSAMPLER_NAMES[:5]}")
    print(f"KSAMPLER_NAMES type: {type(KSAMPLER_NAMES)}")
except ImportError:
    # Fallback sampler list
    KSAMPLER_NAMES = [
        "euler", "euler_cfg_pp", "euler_ancestral", "euler_ancestral_cfg_pp", 
        "heun", "heunpp2", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", 
        "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_2s_ancestral_cfg_pp", 
        "dpmpp_sde", "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_cfg_pp", 
        "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", 
        "ddpm", "lcm", "ipndm", "ipndm_v", "deis", "res_multistep", 
        "res_multistep_cfg_pp", "res_multistep_ancestral", "res_multistep_ancestral_cfg_pp",
        "gradient_estimation", "gradient_estimation_cfg_pp", "er_sde", 
        "seeds_2", "seeds_3", "sa_solver", "sa_solver_pece"
    ]
    print("Using fallback sampler list")

# Try to import ComfyUI scheduler names
try:
    import comfy.samplers
    # Different possible locations for scheduler names
    if hasattr(comfy.samplers, 'SCHEDULER_NAMES'):
        SCHEDULER_NAMES = comfy.samplers.SCHEDULER_NAMES
    elif hasattr(comfy.samplers, 'schedulers'):
        SCHEDULER_NAMES = list(comfy.samplers.schedulers.keys())
    else:
        raise ImportError("No scheduler names found")
    print(f"ComfyUI scheduler names loaded successfully: {len(SCHEDULER_NAMES)} schedulers")
    print(f"Schedulers: {SCHEDULER_NAMES}")
except ImportError:
    # Fallback scheduler list
    SCHEDULER_NAMES = [
        "normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"
    ]
    print("Using fallback scheduler list")

class FloatRangeLoop:
    """
    A node for looping through combinations of cfg and shift float values
    """
    
    # Global counter for sequential mode
    _global_counter = 0
    _last_execution_id = None
    
    RETURN_TYPES = ("FLOAT", "FLOAT", "INT", "INT", "STRING")
    RETURN_NAMES = ("cfg", "shift", "current_index", "total_combinations", "current_combination")
    FUNCTION = "loop_floats"
    CATEGORY = "WanVideo/FloatRange"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cfg_start": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "cfg_end": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "cfg_step": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "shift_start": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "shift_end": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "shift_step": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 10.0, "step": 0.1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "reset": ("BOOLEAN", {"default": False}),
            }
        }

    def loop_floats(self, cfg_start, cfg_end, cfg_step, shift_start, shift_end, shift_step, seed, reset=False):
        """
        Loop through combinations of cfg and shift values sequentially
        """
        import threading
        import time
        
        # Generate cfg values with proper floating point handling
        cfg_values = []
        current_cfg = cfg_start
        while current_cfg <= cfg_end + 1e-10:  # Add small epsilon for floating point comparison
            cfg_values.append(round(current_cfg, 2))
            current_cfg = round(current_cfg + cfg_step, 2)  # Round to avoid floating point drift
        
        # Generate shift values with proper floating point handling
        shift_values = []
        current_shift = shift_start
        while current_shift <= shift_end + 1e-10:  # Add small epsilon for floating point comparison
            shift_values.append(round(current_shift, 2))
            current_shift = round(current_shift + shift_step, 2)  # Round to avoid floating point drift
        
        # Calculate total combinations
        total_combinations = len(cfg_values) * len(shift_values)
        
        if total_combinations == 0:
            return (cfg_start, shift_start, 0, 0)
        
        # Reset counter if requested
        if reset:
            FloatRangeLoop._global_counter = 0
            print(f"FloatRange Loop: counter reset to 0")
        
        # Create a unique execution identifier (timestamp + thread)
        current_execution_id = f"{time.time()}_{threading.current_thread().ident}"
        
        # Only increment if this is a new execution
        if FloatRangeLoop._last_execution_id != current_execution_id:
            FloatRangeLoop._last_execution_id = current_execution_id
            # Don't increment on first call
            if FloatRangeLoop._global_counter > 0 or hasattr(self, '_first_call_done'):
                FloatRangeLoop._global_counter += 1
            else:
                setattr(self, '_first_call_done', True)
        
        step = FloatRangeLoop._global_counter
        
        # Sequential loop through combinations (cycles back to first when complete)
        index = step % total_combinations
        
        # Calculate cfg and shift indices from combined index
        cfg_index = index // len(shift_values)
        shift_index = index % len(shift_values)
        
        selected_cfg = cfg_values[cfg_index]
        selected_shift = shift_values[shift_index]

        current_combination = f"CFG {selected_cfg:.2f}, Shift {selected_shift:.2f}"
        
        # Log current selection for debugging
        print(f"FloatRange Loop: Selected cfg={selected_cfg}, shift={selected_shift} (index: {index}, step: {step}) [Global: {FloatRangeLoop._global_counter}]")
        print(f"  Available cfg values: {cfg_values}")
        print(f"  Available shift values: {shift_values}")
        print(f"  Total combinations: {total_combinations}")
        
        return (selected_cfg, selected_shift, index, total_combinations, current_combination)

class ParametersRangeLoop:
    """
    A node for looping through combinations of cfg, shift, and steps values
    """
    
    # Global counter for sequential mode
    _global_counter = 0
    _last_execution_id = None
    
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", "INT", "INT", "STRING")
    RETURN_NAMES = ("steps", "cfg", "shift" , "current_index", "total_combinations", "current_combination")
    FUNCTION = "loop_parameters"
    CATEGORY = "WanVideo/ParametersRange"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "steps_start": ("INT", {"default": 20, "min": 1, "max": 1000}),
                "steps_end": ("INT", {"default": 50, "min": 1, "max": 1000}),
                "steps_interval": ("INT", {"default": 5, "min": 1, "max": 100}),
                "cfg_start": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "cfg_end": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "cfg_interval": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "shift_start": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "shift_end": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "shift_interval": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 5.0, "step": 0.1}),
                
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "reset": ("BOOLEAN", {"default": False}),
            }
        }

    def loop_parameters(self, cfg_start, cfg_end, cfg_interval, shift_start, shift_end, shift_interval, 
                       steps_start, steps_end, steps_interval, seed=0, reset=False):
        """
        Loop through combinations of cfg, shift, and steps values sequentially
        """
        import threading
        import time
        
        # Error prevention: Check if start values are smaller than end values
        warnings = []
        if cfg_start > cfg_end:
            warnings.append(f"Warning: cfg_start ({cfg_start}) is greater than cfg_end ({cfg_end})")
        if shift_start > shift_end:
            warnings.append(f"Warning: shift_start ({shift_start}) is greater than shift_end ({shift_end})")
        if steps_start > steps_end:
            warnings.append(f"Warning: steps_start ({steps_start}) is greater than steps_end ({steps_end})")
        
        # Print warnings if any
        for warning in warnings:
            print(warning)
        
        # Generate cfg values with proper floating point handling
        cfg_values = []
        current_cfg = cfg_start
        if cfg_start <= cfg_end:
            while current_cfg <= cfg_end + 1e-10:  # Add small epsilon for floating point comparison
                cfg_values.append(round(current_cfg, 2))
                current_cfg = round(current_cfg + cfg_interval, 2)  # Round to avoid floating point drift
        else:
            # If start > end, use only start value
            cfg_values = [cfg_start]
        
        # Generate shift values with proper floating point handling
        shift_values = []
        current_shift = shift_start
        if shift_start <= shift_end:
            while current_shift <= shift_end + 1e-10:  # Add small epsilon for floating point comparison
                shift_values.append(round(current_shift, 2))
                current_shift = round(current_shift + shift_interval, 2)  # Round to avoid floating point drift
        else:
            # If start > end, use only start value
            shift_values = [shift_start]
        
        # Generate steps values (always integers)
        steps_values = []
        if steps_start <= steps_end:
            current_steps = steps_start
            while current_steps <= steps_end:
                steps_values.append(current_steps)
                current_steps += steps_interval
        else:
            # If start > end, use only start value
            steps_values = [steps_start]
        
        # Calculate total combinations
        total_combinations = len(cfg_values) * len(shift_values) * len(steps_values)
        
        if total_combinations == 0:
            return (cfg_start, shift_start, steps_start, 0, 0, 0)
        
        # Reset counter if requested
        if reset:
            ParametersRangeLoop._global_counter = 0
            print(f"Parameters Range Loop: counter reset to 0")
        
        # Create a unique execution identifier (timestamp + thread)
        current_execution_id = f"{time.time()}_{threading.current_thread().ident}"
        
        # Only increment if this is a new execution
        if ParametersRangeLoop._last_execution_id != current_execution_id:
            ParametersRangeLoop._last_execution_id = current_execution_id
            # Don't increment on first call
            if ParametersRangeLoop._global_counter > 0 or hasattr(self, '_first_call_done'):
                ParametersRangeLoop._global_counter += 1
            else:
                setattr(self, '_first_call_done', True)
        
        step = ParametersRangeLoop._global_counter
        
        # Sequential loop through combinations (cycles back to first when complete)
        index = step % total_combinations
        
        # Calculate cfg, shift, and steps indices from combined index
        steps_index = index // (len(cfg_values) * len(shift_values))
        remaining = index % (len(cfg_values) * len(shift_values))
        cfg_index = remaining // len(shift_values)
        shift_index = remaining % len(shift_values)
        
        selected_cfg = cfg_values[cfg_index]
        selected_shift = shift_values[shift_index]
        selected_steps = steps_values[steps_index]

        current_combination = f"{selected_steps} steps, CFG {selected_cfg:.2f}, Shift {selected_shift:.2f}"
        
        # Log current selection for debugging
        print(f"Parameters Range Loop: Selected steps={selected_steps}, cfg={selected_cfg}, shift={selected_shift} (index: {index}, step: {step}) [Global: {ParametersRangeLoop._global_counter}]")
        print(f"  Available cfg values: {cfg_values}")
        print(f"  Available shift values: {shift_values}")
        print(f"  Available steps values: {steps_values}")
        print(f"  Total combinations: {total_combinations}")
        
        return (selected_steps, selected_cfg, selected_shift, index, total_combinations, current_combination)

class SamplerLoop:
    """
    A node that provides automatic looping functionality through ComfyUI samplers
    with internal state management - no manual step increment needed
    """
    
    # Global counters for different modes
    _global_counters = {"sequential": 0, "ping_pong": 0, "random": 0}
    _last_execution_ids = {"sequential": None, "ping_pong": None, "random": None}
    
    RETURN_TYPES = (comfy.samplers.KSampler.SAMPLERS, "INT", "INT", "STRING")
    RETURN_NAMES = ("sampler", "current_index", "total_combinations", "current_combination")
    FUNCTION = "loop_sampler"
    CATEGORY = "Samplers/Loop"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["sequential", "random", "ping_pong"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "reset": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "skip_samplers": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter sampler names to skip, separated by commas:\ne.g., euler, dpm_2, lcm"
                }),
            }
        }

    def loop_sampler(self, mode, seed, reset=False, skip_samplers=""):
        """
        Advanced sampler looping with automatic state management
        """
        import threading
        import time
        
        # Parse skip list from string input
        skip_list = self.parse_skip_list(skip_samplers)
        
        # Filter samplers
        available_samplers = [s for s in KSAMPLER_NAMES if s not in skip_list]
        total_combinations = len(available_samplers)
        
        if not available_samplers:
            # If all samplers are skipped, use full list as fallback
            available_samplers = KSAMPLER_NAMES
            total_combinations = len(KSAMPLER_NAMES)
            print("Warning: All samplers were skipped. Using full sampler list as fallback.")
        
        # Reset counter if requested
        if reset:
            SamplerLoop._global_counters[mode] = 0
            print(f"Sampler Loop: {mode} counter reset to 0")
        
        # Create a unique execution identifier (timestamp + thread + mode)
        current_execution_id = f"{time.time()}_{threading.current_thread().ident}_{mode}"
        
        # Only increment if this is a new execution
        if SamplerLoop._last_execution_ids[mode] != current_execution_id:
            SamplerLoop._last_execution_ids[mode] = current_execution_id
            # Don't increment on first call
            if SamplerLoop._global_counters[mode] > 0 or hasattr(self, f'_first_call_done_{mode}'):
                SamplerLoop._global_counters[mode] += 1
            else:
                setattr(self, f'_first_call_done_{mode}', True)
        
        step = SamplerLoop._global_counters[mode]
        
        if mode == "sequential":
            # Sequential loop through samplers (cycles back to first when complete)
            index = step % len(available_samplers)
            selected_sampler = available_samplers[index]
            
        elif mode == "random":
            # Random selection with seed
            random.seed(seed + step)  # Different random for each step
            selected_sampler = random.choice(available_samplers)
            index = available_samplers.index(selected_sampler)
            
        elif mode == "ping_pong":
            # Ping pong pattern: forward then backward
            cycle_length = len(available_samplers) * 2 - 2
            if cycle_length <= 0:
                cycle_length = 1
            
            pos = step % cycle_length
            if pos < len(available_samplers):
                index = pos
            else:
                index = len(available_samplers) - 2 - (pos - len(available_samplers))
            
            index = max(0, min(index, len(available_samplers) - 1))
            selected_sampler = available_samplers[index]
        
        else:
            # Fallback
            index = 0
            selected_sampler = available_samplers[0]

        current_combination = f"Sampler: {selected_sampler}"
        
        # Log current selection for debugging
        print(f"Sampler Loop: Selected '{selected_sampler}' (index: {index}, step: {step}, mode: {mode}) [Global: {SamplerLoop._global_counters[mode]}]")
        if skip_list:
            print(f"  Skipped samplers: {skip_list}")
        
        return (selected_sampler, index, total_combinations, current_combination)

    def parse_skip_list(self, skip_samplers_str):
        """Parse comma-separated string into list of samplers to skip"""
        if not skip_samplers_str.strip():
            return []
        
        skip_list = []
        for sampler in skip_samplers_str.split(','):
            sampler = sampler.strip()
            if sampler in KSAMPLER_NAMES:
                skip_list.append(sampler)
            elif sampler:  # Only warn for non-empty strings
                print(f"Warning: '{sampler}' is not a valid sampler name")
                print(f"Available samplers: {', '.join(KSAMPLER_NAMES[:10])}...") # Show first 10
        
        return skip_list

class SchedulerLoop:
    """
    A node that provides automatic looping functionality through ComfyUI schedulers
    with internal state management - no manual step increment needed
    """
    
    # Global counters for different modes
    _global_counters = {"sequential": 0, "ping_pong": 0, "random": 0}
    _last_execution_ids = {"sequential": None, "ping_pong": None, "random": None}
    
    RETURN_TYPES = (comfy.samplers.KSampler.SCHEDULERS, "INT", "INT", "STRING")
    RETURN_NAMES = ("scheduler", "current_index", "total_combinations", "current_combination")
    FUNCTION = "loop_scheduler"
    CATEGORY = "Schedulers/Loop"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["sequential", "random", "ping_pong"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "reset": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "skip_schedulers": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter scheduler names to skip, separated by commas:\ne.g., karras, exponential"
                }),
            }
        }

    def loop_scheduler(self, mode, seed, reset=False, skip_schedulers=""):
        """
        Advanced scheduler looping with automatic state management
        """
        import threading
        import time
        
        # Parse skip list from string input
        skip_list = self.parse_skip_list(skip_schedulers)
        
        # Filter schedulers
        available_schedulers = [s for s in SCHEDULER_NAMES if s not in skip_list]
        total_combinations = len(available_schedulers)
        
        if not available_schedulers:
            # If all schedulers are skipped, use full list as fallback
            available_schedulers = SCHEDULER_NAMES
            total_combinations = len(SCHEDULER_NAMES)
            print("Warning: All schedulers were skipped. Using full scheduler list as fallback.")
        
        # Reset counter if requested
        if reset:
            SchedulerLoop._global_counters[mode] = 0
            print(f"Scheduler Loop: {mode} counter reset to 0")
        
        # Create a unique execution identifier (timestamp + thread + mode)
        current_execution_id = f"{time.time()}_{threading.current_thread().ident}_{mode}"
        
        # Only increment if this is a new execution
        if SchedulerLoop._last_execution_ids[mode] != current_execution_id:
            SchedulerLoop._last_execution_ids[mode] = current_execution_id
            # Don't increment on first call
            if SchedulerLoop._global_counters[mode] > 0 or hasattr(self, f'_first_call_done_{mode}'):
                SchedulerLoop._global_counters[mode] += 1
            else:
                setattr(self, f'_first_call_done_{mode}', True)
        
        step = SchedulerLoop._global_counters[mode]
        
        if mode == "sequential":
            # Sequential loop through schedulers (cycles back to first when complete)
            index = step % len(available_schedulers)
            selected_scheduler = available_schedulers[index]
            
        elif mode == "random":
            # Random selection with seed
            random.seed(seed + step)  # Different random for each step
            selected_scheduler = random.choice(available_schedulers)
            index = available_schedulers.index(selected_scheduler)
            
        elif mode == "ping_pong":
            # Ping pong pattern: forward then backward
            cycle_length = len(available_schedulers) * 2 - 2
            if cycle_length <= 0:
                cycle_length = 1
            
            pos = step % cycle_length
            if pos < len(available_schedulers):
                index = pos
            else:
                index = len(available_schedulers) - 2 - (pos - len(available_schedulers))
            
            index = max(0, min(index, len(available_schedulers) - 1))
            selected_scheduler = available_schedulers[index]
        
        else:
            # Fallback
            index = 0
            selected_scheduler = available_schedulers[0]

        current_combination = f"Scheduler: {selected_scheduler}"
        
        # Log current selection for debugging
        print(f"Scheduler Loop: Selected '{selected_scheduler}' (index: {index}, step: {step}, mode: {mode}) [Global: {SchedulerLoop._global_counters[mode]}]")
        if skip_list:
            print(f"  Skipped schedulers: {skip_list}")
        
        return (selected_scheduler, index, total_combinations, current_combination)

    def parse_skip_list(self, skip_schedulers_str):
        """Parse comma-separated string into list of schedulers to skip"""
        if not skip_schedulers_str.strip():
            return []
        
        skip_list = []
        for scheduler in skip_schedulers_str.split(','):
            scheduler = scheduler.strip()
            if scheduler in SCHEDULER_NAMES:
                skip_list.append(scheduler)
            elif scheduler:  # Only warn for non-empty strings
                print(f"Warning: '{scheduler}' is not a valid scheduler name")
                print(f"Available schedulers: {', '.join(SCHEDULER_NAMES)}")
        
        return skip_list

class SamplerSchedulerLoop:
    """
    A node that provides automatic looping functionality through combinations of 
    ComfyUI samplers and schedulers with internal state management
    """
    
    # Global counters for different modes
    _global_counters = {"sequential": 0, "ping_pong": 0, "random": 0}
    _last_execution_ids = {"sequential": None, "ping_pong": None, "random": None}
    
    RETURN_TYPES = (comfy.samplers.KSampler.SAMPLERS, comfy.samplers.KSampler.SCHEDULERS, "INT", "INT", "STRING")
    RETURN_NAMES = ("sampler", "scheduler", "current_index", "total_combinations", "current_combination")
    FUNCTION = "loop_sampler_scheduler"
    CATEGORY = "Samplers/Loop"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["sequential", "random", "ping_pong"],),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "reset": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "skip_samplers": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter sampler names to skip, separated by commas:\ne.g., euler, dpm_2, lcm"
                }),
                "skip_schedulers": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter scheduler names to skip, separated by commas:\ne.g., karras, exponential"
                }),
            }
        }

    def loop_sampler_scheduler(self, mode, seed, reset=False, skip_samplers="", skip_schedulers=""):
        """
        Advanced sampler and scheduler combination looping with automatic state management
        """
        import threading
        import time
        
        # Parse skip lists from string inputs
        skip_samplers_list = self.parse_skip_list(skip_samplers, KSAMPLER_NAMES, "sampler")
        skip_schedulers_list = self.parse_skip_list(skip_schedulers, SCHEDULER_NAMES, "scheduler")
        
        # Filter samplers and schedulers
        available_samplers = [s for s in KSAMPLER_NAMES if s not in skip_samplers_list]
        available_schedulers = [s for s in SCHEDULER_NAMES if s not in skip_schedulers_list]
        
        if not available_samplers:
            available_samplers = KSAMPLER_NAMES
            print("Warning: All samplers were skipped. Using full sampler list as fallback.")
        
        if not available_schedulers:
            available_schedulers = SCHEDULER_NAMES
            print("Warning: All schedulers were skipped. Using full scheduler list as fallback.")
        
        # Calculate total combinations
        total_combinations = len(available_samplers) * len(available_schedulers)
        
        # Reset counter if requested
        if reset:
            SamplerSchedulerLoop._global_counters[mode] = 0
            print(f"Sampler Scheduler Loop: {mode} counter reset to 0")
        
        # Create a unique execution identifier (timestamp + thread + mode)
        current_execution_id = f"{time.time()}_{threading.current_thread().ident}_{mode}"
        
        # Only increment if this is a new execution
        if SamplerSchedulerLoop._last_execution_ids[mode] != current_execution_id:
            SamplerSchedulerLoop._last_execution_ids[mode] = current_execution_id
            # Don't increment on first call
            if SamplerSchedulerLoop._global_counters[mode] > 0 or hasattr(self, f'_first_call_done_{mode}'):
                SamplerSchedulerLoop._global_counters[mode] += 1
            else:
                setattr(self, f'_first_call_done_{mode}', True)
        
        step = SamplerSchedulerLoop._global_counters[mode]
        
        if mode == "sequential":
            # Sequential loop through combinations
            index = step % total_combinations
            
        elif mode == "random":
            # Random selection with seed
            random.seed(seed + step)  # Different random for each step
            index = random.randint(0, total_combinations - 1)
            
        elif mode == "ping_pong":
            # Ping pong pattern: forward then backward
            cycle_length = total_combinations * 2 - 2
            if cycle_length <= 0:
                cycle_length = 1
            
            pos = step % cycle_length
            if pos < total_combinations:
                index = pos
            else:
                index = total_combinations - 2 - (pos - total_combinations)
            
            index = max(0, min(index, total_combinations - 1))
        
        else:
            # Fallback
            index = 0
        
        # Calculate sampler and scheduler indices from combined index
        sampler_index = index // len(available_schedulers)
        scheduler_index = index % len(available_schedulers)
        
        selected_sampler = available_samplers[sampler_index]
        selected_scheduler = available_schedulers[scheduler_index]
        
        current_combination = f"Sampler: {selected_sampler}, Scheduler: {selected_scheduler}"
        
        # Log current selection for debugging
        print(f"Sampler Scheduler Loop: Selected sampler='{selected_sampler}', scheduler='{selected_scheduler}' (index: {index}, step: {step}, mode: {mode}) [Global: {SamplerSchedulerLoop._global_counters[mode]}]")
        if skip_samplers_list or skip_schedulers_list:
            print(f"  Skipped samplers: {skip_samplers_list}")
            print(f"  Skipped schedulers: {skip_schedulers_list}")
        
        return (selected_sampler, selected_scheduler, index, total_combinations, current_combination)

    def parse_skip_list(self, skip_str, available_list, item_type):
        """Parse comma-separated string into list of items to skip"""
        if not skip_str.strip():
            return []
        
        skip_list = []
        for item in skip_str.split(','):
            item = item.strip()
            if item in available_list:
                skip_list.append(item)
            elif item:  # Only warn for non-empty strings
                print(f"Warning: '{item}' is not a valid {item_type} name")
                print(f"Available {item_type}s: {', '.join(available_list)}")
        
        return skip_list

class AllParametersLoop:
    """
    A comprehensive node that combines sampler, scheduler, and parameter range looping
    Loops through combinations of steps, cfg, shift, samplers, and schedulers
    """
    
    # Global counters for different modes
    _global_counters = {"sequential": 0, "ping_pong": 0, "random": 0}
    _last_execution_ids = {"sequential": None, "ping_pong": None, "random": None}
    
    RETURN_TYPES = ("INT", "FLOAT", "FLOAT", comfy.samplers.KSampler.SAMPLERS, comfy.samplers.KSampler.SCHEDULERS, "INT", "INT", "STRING")
    RETURN_NAMES = ("steps", "cfg", "shift", "sampler", "scheduler", "current_index", "total_combinations", "current_combination")
    FUNCTION = "loop_all_parameters"
    CATEGORY = "Samplers/Loop"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["sequential", "random", "ping_pong"],),
                # Steps parameters
                "steps_start": ("INT", {"default": 20, "min": 1, "max": 1000}),
                "steps_end": ("INT", {"default": 50, "min": 1, "max": 1000}),
                "steps_interval": ("INT", {"default": 10, "min": 1, "max": 100}),
                # CFG parameters
                "cfg_start": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "cfg_end": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 30.0, "step": 0.1}),
                "cfg_interval": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                # Shift parameters
                "shift_start": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "shift_end": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "shift_interval": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 5.0, "step": 0.1}),
                # Control parameters
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "reset": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "skip_samplers": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter sampler names to skip, separated by commas:\ne.g., euler, dpm_2, lcm"
                }),
                "skip_schedulers": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter scheduler names to skip, separated by commas:\ne.g., karras, exponential"
                }),
            }
        }

    def loop_all_parameters(self, mode, steps_start, steps_end, steps_interval,
                           cfg_start, cfg_end, cfg_interval, shift_start, shift_end, shift_interval,
                           seed=0, reset=False, skip_samplers="", skip_schedulers=""):
        """
        Advanced looping combining sampler, scheduler selection with parameter ranges
        """
        import threading
        import time
        
        # Error prevention: Check if start values are smaller than end values
        warnings = []
        if cfg_start > cfg_end:
            warnings.append(f"Warning: cfg_start ({cfg_start}) is greater than cfg_end ({cfg_end})")
        if shift_start > shift_end:
            warnings.append(f"Warning: shift_start ({shift_start}) is greater than shift_end ({shift_end})")
        if steps_start > steps_end:
            warnings.append(f"Warning: steps_start ({steps_start}) is greater than steps_end ({steps_end})")
        
        # Print warnings if any
        for warning in warnings:
            print(warning)
        
        # Parse skip lists from string inputs
        skip_samplers_list = self.parse_skip_list(skip_samplers, KSAMPLER_NAMES, "sampler")
        skip_schedulers_list = self.parse_skip_list(skip_schedulers, SCHEDULER_NAMES, "scheduler")
        
        # Filter samplers and schedulers
        available_samplers = [s for s in KSAMPLER_NAMES if s not in skip_samplers_list]
        available_schedulers = [s for s in SCHEDULER_NAMES if s not in skip_schedulers_list]
        
        if not available_samplers:
            available_samplers = KSAMPLER_NAMES
            print("Warning: All samplers were skipped. Using full sampler list as fallback.")
        
        if not available_schedulers:
            available_schedulers = SCHEDULER_NAMES
            print("Warning: All schedulers were skipped. Using full scheduler list as fallback.")
        
        # Generate parameter values with proper floating point handling
        # Steps values (always integers)
        steps_values = []
        if steps_start <= steps_end:
            current_steps = steps_start
            while current_steps <= steps_end:
                steps_values.append(current_steps)
                current_steps += steps_interval
        else:
            steps_values = [steps_start]
        
        # CFG values
        cfg_values = []
        current_cfg = cfg_start
        if cfg_start <= cfg_end:
            while current_cfg <= cfg_end + 1e-10:  # Add small epsilon for floating point comparison
                cfg_values.append(round(current_cfg, 2))
                current_cfg = round(current_cfg + cfg_interval, 2)  # Round to avoid floating point drift
        else:
            cfg_values = [cfg_start]
        
        # Shift values
        shift_values = []
        current_shift = shift_start
        if shift_start <= shift_end:
            while current_shift <= shift_end + 1e-10:  # Add small epsilon for floating point comparison
                shift_values.append(round(current_shift, 2))
                current_shift = round(current_shift + shift_interval, 2)  # Round to avoid floating point drift
        else:
            shift_values = [shift_start]
        
        # Calculate total combinations
        total_combinations = len(steps_values) * len(cfg_values) * len(shift_values) * len(available_samplers) * len(available_schedulers)
        
        if total_combinations == 0:
            return (steps_start, cfg_start, shift_start, available_samplers[0] if available_samplers else KSAMPLER_NAMES[0],
                    available_schedulers[0] if available_schedulers else SCHEDULER_NAMES[0], 0, 0, "")
        
        # Reset counter if requested
        if reset:
            AllParametersLoop._global_counters[mode] = 0
            print(f"All Parameters Loop: {mode} counter reset to 0")
        
        # Create a unique execution identifier (timestamp + thread + mode)
        current_execution_id = f"{time.time()}_{threading.current_thread().ident}_{mode}"
        
        # Only increment if this is a new execution
        if AllParametersLoop._last_execution_ids[mode] != current_execution_id:
            AllParametersLoop._last_execution_ids[mode] = current_execution_id
            # Don't increment on first call
            if AllParametersLoop._global_counters[mode] > 0 or hasattr(self, f'_first_call_done_{mode}'):
                AllParametersLoop._global_counters[mode] += 1
            else:
                setattr(self, f'_first_call_done_{mode}', True)
        
        step = AllParametersLoop._global_counters[mode]
        
        if mode == "sequential":
            # Sequential loop through all combinations
            index = step % total_combinations
            
        elif mode == "random":
            # Random selection with seed
            random.seed(seed + step)  # Different random for each step
            index = random.randint(0, total_combinations - 1)
            
        elif mode == "ping_pong":
            # Ping pong pattern: forward then backward
            cycle_length = total_combinations * 2 - 2
            if cycle_length <= 0:
                cycle_length = 1
            
            pos = step % cycle_length
            if pos < total_combinations:
                index = pos
            else:
                index = total_combinations - 2 - (pos - total_combinations)
            
            index = max(0, min(index, total_combinations - 1))
        
        else:
            # Fallback
            index = 0
        
        # Calculate individual indices from combined index
        # Order: steps -> cfg -> shift -> sampler -> scheduler
        scheduler_index = index // (len(steps_values) * len(cfg_values) * len(shift_values) * len(available_samplers))
        remaining = index % (len(steps_values) * len(cfg_values) * len(shift_values) * len(available_samplers))
        
        sampler_index = remaining // (len(steps_values) * len(cfg_values) * len(shift_values))
        remaining = remaining % (len(steps_values) * len(cfg_values) * len(shift_values))
        
        shift_index = remaining // (len(steps_values) * len(cfg_values))
        remaining = remaining % (len(steps_values) * len(cfg_values))
        
        cfg_index = remaining // len(steps_values)
        steps_index = remaining % len(steps_values)
        
        selected_steps = steps_values[steps_index]
        selected_cfg = cfg_values[cfg_index]
        selected_shift = shift_values[shift_index]
        selected_sampler = available_samplers[sampler_index]
        selected_scheduler = available_schedulers[scheduler_index]
        
        current_combination = f"{selected_steps} steps, CFG {selected_cfg:.2f}, Shift {selected_shift:.2f}, {selected_sampler}, {selected_scheduler}"
        
        # Log current selection for debugging
        print(f"All Parameters Loop: Selected steps={selected_steps}, cfg={selected_cfg}, shift={selected_shift}, sampler='{selected_sampler}', scheduler='{selected_scheduler}' (index: {index}, step: {step}, mode: {mode}) [Global: {AllParametersLoop._global_counters[mode]}]")
        print(f"  Total combinations: {total_combinations}")
        if skip_samplers_list or skip_schedulers_list:
            print(f"  Skipped samplers: {skip_samplers_list}")
            print(f"  Skipped schedulers: {skip_schedulers_list}")
        
        return (selected_steps, selected_cfg, selected_shift, selected_sampler, selected_scheduler, index, total_combinations, current_combination)

    def parse_skip_list(self, skip_str, available_list, item_type):
        """Parse comma-separated string into list of items to skip"""
        if not skip_str.strip():
            return []
        
        skip_list = []
        for item in skip_str.split(','):
            item = item.strip()
            if item in available_list:
                skip_list.append(item)
            elif item:  # Only warn for non-empty strings
                print(f"Warning: '{item}' is not a valid {item_type} name")
                print(f"Available {item_type}s: {', '.join(available_list)}")
        
        return skip_list

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "FloatRangeLoop": FloatRangeLoop,
    "ParametersRangeLoop": ParametersRangeLoop,
    "SamplerLoop": SamplerLoop,
    "SchedulerLoop": SchedulerLoop,
    "SamplerSchedulerLoop": SamplerSchedulerLoop,
    "AllParametersLoop": AllParametersLoop,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FloatRangeLoop": "Float Range Loop",
    "ParametersRangeLoop": "Parameters Range Loop",
    "SamplerLoop": "Sampler Loop",
    "SchedulerLoop": "Scheduler Loop", 
    "SamplerSchedulerLoop": "Sampler Scheduler Loop",
    "AllParametersLoop": "All Parameters Loop",
}