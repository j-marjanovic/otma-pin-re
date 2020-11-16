

module base_project (
  inout test_pin
);

wire [1:0] sources;
wire [0:0] probes;

io_tester inst_io_tester (
    .source ( sources ),
    .probe  ( probes  )
);

assign test_pin = sources[1] ? 1'bz : sources[0];
assign probes[0] = test_pin;

endmodule
