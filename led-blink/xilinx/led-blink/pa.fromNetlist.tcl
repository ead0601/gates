
# PlanAhead Launch Script for Post-Synthesis floorplanning, created by Project Navigator

create_project -name led-blink -dir "/build/repo/gates/led-blink/xilinx/led-blink/planAhead_run_2" -part xc6slx16ftg256-3
set_property design_mode GateLvl [get_property srcset [current_run -impl]]
set_property edif_top_file "/build/repo/gates/led-blink/xilinx/led-blink/led_test.ngc" [ get_property srcset [ current_run ] ]
add_files -norecurse { {/build/repo/gates/led-blink/xilinx/led-blink} }
set_property target_constrs_file "led.ucf" [current_fileset -constrset]
add_files [list {led.ucf}] -fileset [get_property constrset [current_run]]
link_design
