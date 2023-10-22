
# PlanAhead Launch Script for Post-Synthesis floorplanning, created by Project Navigator

create_project -name uartloop-top -dir "/build/repo/gates/uart-test/xilinx/uartloop-top/planAhead_run_1" -part xc6slx16ftg256-3
set_property design_mode GateLvl [get_property srcset [current_run -impl]]
set_property edif_top_file "/build/repo/gates/uart-test/xilinx/uartloop-top/uartloop_top.ngc" [ get_property srcset [ current_run ] ]
add_files -norecurse { {/build/repo/gates/uart-test/xilinx/uartloop-top} }
set_property target_constrs_file "uartloop_top.ucf" [current_fileset -constrset]
add_files [list {uartloop_top.ucf}] -fileset [get_property constrset [current_run]]
link_design
