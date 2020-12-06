

module base_project (
  output test_pin
);

(*keep*) wire osc0, osc1, osc2;

not u0(osc1, osc0);
not u1(osc2, osc1);
not u2(osc0, osc2);

assign test_pin = osc0;

endmodule
