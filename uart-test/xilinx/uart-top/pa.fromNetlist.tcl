
# PlanAhead Launch Script for Post-Synthesis floorplanning, created by Project Navigator

create_project -name uart-top -dir "/build/repo/gates/sdio-reader/xilinx/uart-top/planAhead_run_2" -part xc6slx16ftg256-3
set_property design_mode GateLvl [get_property srcset [current_run -impl]]
set_property edif_top_file "/build/repo/gates/sdio-reader/xilinx/uart-top/uart_top.ngc" [ get_property srcset [ current_run ] ]
add_files -norecurse { {/build/repo/gates/sdio-reader/xilinx/uart-top} }
set_property target_constrs_file "uart_top.ucf" [current_fileset -constrset]
add_files [list {uart_top.ucf}] -fileset [get_property constrset [current_run]]
link_design
