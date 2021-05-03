
module pcie_top (
    input        PCIE_CLK,
    
    input        PCIE_PERST,
    
    input  [7:0] PCIE_RX,
    output [7:0] PCIE_TX
);

system_pcie u0 (
    .pcie1_refclk_clk         (   PCIE_CLK ),
    .pcie1_hip_serial_rx_in0  ( PCIE_RX[0] ),
    .pcie1_hip_serial_rx_in1  ( PCIE_RX[1] ),
    .pcie1_hip_serial_rx_in2  ( PCIE_RX[2] ),
    .pcie1_hip_serial_rx_in3  ( PCIE_RX[3] ),
    .pcie1_hip_serial_rx_in4  ( PCIE_RX[4] ),
    .pcie1_hip_serial_rx_in5  ( PCIE_RX[5] ),
    .pcie1_hip_serial_rx_in6  ( PCIE_RX[6] ),
    .pcie1_hip_serial_rx_in7  ( PCIE_RX[7] ),
    .pcie1_hip_serial_tx_out0 ( PCIE_TX[0] ),
    .pcie1_hip_serial_tx_out1 ( PCIE_TX[1] ),
    .pcie1_hip_serial_tx_out2 ( PCIE_TX[2] ),
    .pcie1_hip_serial_tx_out3 ( PCIE_TX[3] ),
    .pcie1_hip_serial_tx_out4 ( PCIE_TX[4] ),
    .pcie1_hip_serial_tx_out5 ( PCIE_TX[5] ),
    .pcie1_hip_serial_tx_out6 ( PCIE_TX[6] ),
    .pcie1_hip_serial_tx_out7 ( PCIE_TX[7] ),
    .pcie1_npor_npor          (       1'b1 ),
    .pcie1_npor_pin_perst     ( PCIE_PERST )
);

endmodule

