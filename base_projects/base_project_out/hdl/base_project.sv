

module base_project_osc  (
    output osc_out
);

(*keep*) wire osc0, osc1, osc2;

not u0(osc1, osc0);
not u1(osc2, osc1);
not u2(osc0, osc2);

assign osc_out = osc0;

endmodule


module base_project (
  output test_pin
);

base_project_osc inst_osc (
    .osc_out (test_pin)
);

endmodule
