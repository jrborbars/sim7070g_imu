"""SIM7070G (OpenCPU) + LSM6DSV16X + 1S LiPo board (circuit-synth).

Authoritative sources used
--------------------------
* SIM7070 Series Hardware Design V1.03 - Table 3 (68-pin map), Table 5
  (pin description), Tables 43/44 (schematic + layout check lists),
  Figure 4 (footprint), Figure 37 (stencil).
* ETA6095 datasheet (8 pp) - ISET 0.8V, 150k=1.2A / 82k=2A, CV 4.21V,
  precharge 2.9V/200mA, termination 130mA, recharge -160mV, STAT low =
  charging / Hi-Z = done. NO TS/NTC pin, NO JEITA, NO SYS/load-sharing.
* LSM6DSV16X pinout extracted from the SnapEDA symbol shipped in
  lsm6dsv16x-xiao-main.tar.gz (LSM6DSV16XTR -> XDCR_LSM6DSV16XTR).

Facts that drive this schematic (all verified in the sources above)
------------------------------------------------------------------
* The SIM7070G has NO dedicated RESET pin: reset is a >12.6s PWRKEY
  long-press. There is also NO dedicated SIM_DET pin, so card detect
  must land on a GPIO.
* Pins 55/56/57 are all VBAT and 15 pads are GND; the footprint
  collapses them to pad numbers 55 and 2 so that one symbol pin drives
  each rail (standard practice for module footprints).
* "BOOT_CFG and GPIO1 cannot be pulled up" before normal power-up, so
  the IMU interrupts are NOT parked on GPIO1, and BOOT_CFG gets no
  pull-up (only a DNP jumper to GND plus a test point).
* GPIO/I2C/UART/USB logic is 1.8V; VDD_EXT (pin 15) is a 1.8V, 50mA
  reference only, so it biases the I2C pull-ups and the IMU VDDIO while
  the IMU analog rail gets its own low-Iq LDO.
* I2C must be pulled up with 1K resistors to VDD_EXT (check list #9).
* VBAT trace must be wider than 2mm (check list #2) and the VBAT bank
  must hold the drop under 300mV, hence 3x100uF + 1uF + TVS at the pins.
* TVS junction capacitance must be <3pF on USB DP/DM and <50pF on the
  SIM lines; the SIM trace must pass through the TVS pad before the
  module pad, with no stubs.
* LTE main ANT needs a low-capacitance TVS and a PI matching network;
  the shunt elements stay DNP until VNA tuning.

Layout constraints (documented here, enforced by hand/DRC)
---------------------------------------------------------
Stack L1 Sig / L2 GND continuous / L3 PWR / L4 Sig, 1.6mm FR4.
RF on L1 referenced to L2, PI network hard against ANT_MAIN/GNSS_ANT,
keep-out 3x trace width, USB as a 90R pair with dL < 0.15mm, and
TRACE_W_50R_MM is a parameter to be recomputed for the chosen fab
prepreg (Er ~4.2) - not a final number.
"""

from circuit_synth import Circuit, Component, Net, circuit

TRACE_W_50R_MM = 0.35  # param: recompute per fab stackup + VNA tune


@circuit(name="sim7070g_imu_batt")
def board():
    # --- ICs -------------------------------------------------------
    modem = Component(symbol="sim7070g:SIM7070G", ref="U1",
                      value="SIM7070G",
                      footprint="sim7070g_imu_batt:SIM7070G_LCC_LGA68")
    charger = Component(symbol="eta6095:ETA6095", ref="U2",
                        value="ETA6095",
                        footprint="Package_DFN_QFN:"
                                  "DFN-8-1EP_2x3mm_P0.5mm_EP0.61x2.2mm")
    imu = Component(symbol="lsm6dsv16x:LSM6DSV16X", ref="U3",
                    value="LSM6DSV16X",
                    footprint="sim7070g_imu_batt:LSM6DSV16X_LGA14")
    ldo_imu = Component(symbol="ldo_nanoiq:NanoIq_LDO_2V5", ref="U4",
                        value="NanoIq_LDO_2V5",
                        footprint="Package_TO_SOT_SMD:SOT-23-5")
    fuel = Component(symbol="Timer_RTC:PCF8523T", ref="U6",
                     value="MAX17048_DNP",
                     footprint="Package_DFN_QFN:"
                               "DFN-8-1EP_3x3mm_P0.5mm_EP1.65x2.38mm",
                     dnp=True)

    # --- Connectors ------------------------------------------------
    usb = Component(symbol="Connector:USB_C_Receptacle_USB2.0_16P", ref="J1",
                    value="USB-C-16P",
                    footprint="Connector_USB:"
                              "USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A")
    sim = Component(symbol="nanosim:NanoSIM_PushPush_GCT_SIM8060", ref="J2",
                    value="NanoSIM",
                    footprint="sim7070g_imu_batt:"
                              "NanoSIM_GCT_SIM8060-6-1")
    ufl_lte = Component(symbol="Connector:Conn_Coaxial", ref="J3",
                        value="U.FL_LTE",
                        footprint="Connector_Coaxial:"
                                  "U.FL_Hirose_U.FL-R-SMT-1_Vertical")
    ufl_gnss = Component(symbol="Connector:Conn_Coaxial", ref="J4",
                         value="U.FL_GNSS",
                         footprint="Connector_Coaxial:"
                                   "U.FL_Hirose_U.FL-R-SMT-1_Vertical")
    bat = Component(symbol="Connector_Generic:Conn_01x02", ref="J5",
                    value="BAT_SOLDER_PADS",
                    footprint="sim7070g_imu_batt:BAT_SolderPads")

    # --- Protection ------------------------------------------------
    esd_sim = Component(symbol="Power_Protection:ESDA6V1-5SC6", ref="D1",
                        value="ESDA6V1",
                        footprint="Package_TO_SOT_SMD:SOT-666")
    tvs_vbat = Component(symbol="Device:D", ref="D2",
                         value="TVS_PESDHC2FD4V5B",
                         footprint="Diode_SMD:D_SOD-882")
    esd_usb = Component(symbol="Power_Protection:USBLC6-2P6", ref="D3",
                        value="USBLC6-2P6",
                        footprint="Package_TO_SOT_SMD:SOT-23-6")
    tvs_ant = Component(symbol="Device:D", ref="D4",
                        value="TVS_LOWCAP_ANT",
                        footprint="Diode_SMD:D_0402_1005Metric", dnp=True)

    # --- VBAT bank: 300uF total, TVS + 1uF hard against the module pins
    c_vb1 = Component(symbol="Device:C", ref="C1", value="1uF",
                      footprint="Capacitor_SMD:C_0402_1005Metric")
    c_vbb1 = Component(symbol="Device:C", ref="C2", value="100uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    c_vbb2 = Component(symbol="Device:C", ref="C3", value="100uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    c_vbb3 = Component(symbol="Device:C", ref="C16", value="100uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")

    # --- Charger / USB-C input -------------------------------------
    c_u1 = Component(symbol="Device:C", ref="C4", value="22uF",
                     footprint="Capacitor_SMD:C_0603_1608Metric")
    c_u2 = Component(symbol="Device:C", ref="C5", value="22uF",
                     footprint="Capacitor_SMD:C_0603_1608Metric")
    l_chg = Component(symbol="Device:L", ref="L1", value="2.2uH",
                      footprint="Inductor_SMD:L_1008_2520Metric")

    # --- SIM: 100nF + 22pF right at the holder ---------------------
    c_vs1 = Component(symbol="Device:C", ref="C6", value="100nF",
                      footprint="Capacitor_SMD:C_0402_1005Metric")
    c_vs2 = Component(symbol="Device:C", ref="C7", value="22pF",
                      footprint="Capacitor_SMD:C_0402_1005Metric")

    # --- IMU decoupling --------------------------------------------
    c_im1 = Component(symbol="Device:C", ref="C8", value="100nF",
                      footprint="Capacitor_SMD:C_0402_1005Metric")
    c_im2 = Component(symbol="Device:C", ref="C9", value="1uF",
                      footprint="Capacitor_SMD:C_0402_1005Metric")
    c_li = Component(symbol="Device:C", ref="C10", value="1uF",
                     footprint="Capacitor_SMD:C_0402_1005Metric")
    c_lo = Component(symbol="Device:C", ref="C11", value="1uF",
                     footprint="Capacitor_SMD:C_0402_1005Metric")

    # --- RF PI networks: series 0R populated, shunts DNP for VNA ---
    r_pilte = Component(symbol="Device:R", ref="R8", value="0R",
                        footprint="Resistor_SMD:R_0402_1005Metric")
    r_pignss = Component(symbol="Device:R", ref="R9", value="0R",
                         footprint="Resistor_SMD:R_0402_1005Metric")
    c_pilte_a = Component(symbol="Device:C", ref="C12", value="DNP_SHUNT",
                          footprint="Capacitor_SMD:C_0402_1005Metric",
                          dnp=True)
    c_pilte_b = Component(symbol="Device:C", ref="C13", value="DNP_SHUNT",
                          footprint="Capacitor_SMD:C_0402_1005Metric",
                          dnp=True)
    c_pignss_a = Component(symbol="Device:C", ref="C14", value="DNP_SHUNT",
                           footprint="Capacitor_SMD:C_0402_1005Metric",
                           dnp=True)
    c_pignss_b = Component(symbol="Device:C", ref="C15", value="DNP_SHUNT",
                           footprint="Capacitor_SMD:C_0402_1005Metric",
                           dnp=True)

    # --- Straps / pull-ups -----------------------------------------
    r_iset = Component(symbol="Device:R", ref="R1", value="180k",
                       footprint="Resistor_SMD:R_0402_1005Metric")
    r_cc1 = Component(symbol="Device:R", ref="R2", value="5.1k",
                      footprint="Resistor_SMD:R_0402_1005Metric")
    r_cc2 = Component(symbol="Device:R", ref="R3", value="5.1k",
                      footprint="Resistor_SMD:R_0402_1005Metric")
    # 1K to VDD_EXT per HW Design check list #9 (not 4.7K).
    r_sda = Component(symbol="Device:R", ref="R4", value="1k",
                      footprint="Resistor_SMD:R_0402_1005Metric")
    r_scl = Component(symbol="Device:R", ref="R5", value="1k",
                      footprint="Resistor_SMD:R_0402_1005Metric")
    r_det = Component(symbol="Device:R", ref="R6", value="10k",
                      footprint="Resistor_SMD:R_0402_1005Metric")
    # BOOT_CFG must stay open before boot: jumper to GND only, DNP.
    r_boot = Component(symbol="Device:R", ref="R7", value="0R_JMP_GND",
                       footprint="Resistor_SMD:R_0402_1005Metric", dnp=True)
    # DTR must be pulled up when the module enters sleep (check list #12),
    # so this one is POPULATED, not DNP.
    r_dtr = Component(symbol="Device:R", ref="R13", value="10k",
                      footprint="Resistor_SMD:R_0402_1005Metric")
    # INT series isolation, DNP until EMC/level checked.
    r_i1 = Component(symbol="Device:R", ref="R10", value="0R",
                     footprint="Resistor_SMD:R_0402_1005Metric", dnp=True)
    r_i2 = Component(symbol="Device:R", ref="R11", value="0R",
                     footprint="Resistor_SMD:R_0402_1005Metric", dnp=True)

    # --- NTC / fuel-gauge reserves (zero cost while DNP) -----------
    r_ntc = Component(symbol="Device:R", ref="RT1", value="NTC_10k_B3380",
                      footprint="Resistor_SMD:R_0402_1005Metric", dnp=True)
    r_sns = Component(symbol="Device:R", ref="R12", value="0R",
                      footprint="Resistor_SMD:R_0603_1608Metric")

    # --- Debug / flash breakout test points ------------------------
    # HW Design note: "reserve a test point for BOOT_CFG and VDD_EXT.
    # If there is no USB connector, please also reserve a test point for
    # USB_VBUS, USB_DP and USB_DM for firmware upgrade."
    # We keep the USB-C, so USB lines break out through J1; these TPs
    # cover the UART/status handshake needed to flash and to debug a
    # hung OpenCPU application over AT commands.
    # NOTE: the SIM7070G has NO reset pin - a PWRKEY low pulse >12.6s is
    # the hardware reset, so PWRKEY is the "reset" breakout here.
    tp_pwrkey = Component(symbol="Connector:TestPoint", ref="TP1",
                          value="TP_PWRKEY",
                          footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_txd = Component(symbol="Connector:TestPoint", ref="TP2",
                       value="TP_UART1_TXD",
                       footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_rxd = Component(symbol="Connector:TestPoint", ref="TP3",
                       value="TP_UART1_RXD",
                       footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_dbgtx = Component(symbol="Connector:TestPoint", ref="TP4",
                         value="TP_DEBUG_TXD",
                         footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_dbgrx = Component(symbol="Connector:TestPoint", ref="TP5",
                         value="TP_DEBUG_RXD",
                         footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_stat = Component(symbol="Connector:TestPoint", ref="TP6",
                        value="TP_STATUS",
                        footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_chg = Component(symbol="Connector:TestPoint", ref="TP7",
                       value="TP_CHG_STAT",
                       footprint="TestPoint:TestPoint_Pad_D1.5mm")
    tp_vddext = Component(symbol="Connector:TestPoint", ref="TP8",
                          value="TP_VDD_EXT",
                          footprint="TestPoint:TestPoint_Pad_D1.5mm")


    # ================= NETS =================
    # BAT_PACK: the holder pad and one side of R12. R12 is a series 0R so a
    # bench ammeter (or a real shunt) can be inserted between the pack and
    # the rail without cutting a trace. MAX17048 is a ModelGauge part and
    # needs no sense resistor, so R12 must NOT be strapped across VBAT.
    bat_pack = Net("BAT_PACK")
    bat[1] += bat_pack
    r_sns[1] += bat_pack

    # VBAT star: battery node feeds the SIM7070G VBAT pins directly (not
    # a charger SYS rail) so 2A TX bursts never brown out on cable drop.
    vbat = Net("VBAT")
    r_sns[2] += vbat
    l_chg[2] += vbat
    charger["BATS"] += vbat
    tvs_vbat[1] += vbat
    modem["VBAT"] += vbat          # pins 55/56/57, >2mm trace
    c_vb1[1] += vbat
    c_vbb1[1] += vbat
    c_vbb2[1] += vbat
    c_vbb3[1] += vbat
    ldo_imu["IN"] += vbat
    c_li[1] += vbat
    fuel["VBAT"] += vbat
    fuel["VDD"] += vbat          # MAX17048 runs from the pack, not 1.8V
    r_ntc[1] += vbat

    gnd = Net("GND", is_power=False, power_symbol=None)
    bat[2] += gnd
    tvs_vbat[2] += gnd
    c_vb1[2] += gnd
    c_vbb1[2] += gnd
    c_vbb2[2] += gnd
    c_vbb3[2] += gnd
    charger["AGND"] += gnd
    charger["PGND"] += gnd
    charger["OTG"] += gnd          # OTG=0 -> force buck, no boost mode
    modem["GND"] += gnd            # 15 pads + centre thermal pad
    c_u1[2] += gnd
    c_u2[2] += gnd
    esd_sim["GND"] += gnd
    esd_usb["GND"] += gnd
    sim["GND"] += gnd
    sim["SHIELD"] += gnd
    sim["VPP"] += gnd              # nano-SIM has no VPP contact; tie low
    imu["GND"] += gnd
    c_im1[2] += gnd
    c_im2[2] += gnd
    c_vs1[2] += gnd
    c_vs2[2] += gnd
    ldo_imu["GND"] += gnd
    c_lo[2] += gnd
    fuel["VSS"] += gnd
    r_iset[2] += gnd
    r_boot[2] += gnd               # BOOT_CFG -> GND jumper, DNP
    r_ntc[2] += gnd
    c_pilte_a[2] += gnd
    c_pilte_b[2] += gnd
    c_pignss_a[2] += gnd
    c_pignss_b[2] += gnd
    usb["GND"] += gnd
    usb["SHIELD"] += gnd
    ufl_lte["Ext"] += gnd
    ufl_gnss["Ext"] += gnd
    tvs_ant[2] += gnd

    usb5v = Net("USB_5V")
    usb["VBUS"] += usb5v
    charger["USB"] += usb5v
    esd_usb["VBUS"] += usb5v
    c_u1[1] += usb5v
    c_u2[1] += usb5v
    # USB-C sink: CC1/CC2 each need their own 5.1k Rd to GND (NOT to VBUS).
    # Wiring these to 5V would present a source signature and break
    # negotiation with the host/charger.
    r_cc1[1] += gnd
    r_cc2[1] += gnd
    # USB_VBUS (pin 24) is the module's USB detection input AND the
    # emergency-download trigger; it must see the 5V rail.
    modem["USB_VBUS"] += usb5v

    iset = Net("ISET")
    charger["ISET"] += iset
    r_iset[1] += iset              # 180k ~ 1A charge (1C of 1000mAh)

    stat = Net("CHG_STAT")         # STAT is open-drain, low while charging
    charger["STAT"] += stat        # -> castellated test point

    # VDD_EXT (1.8V, 50mA, reference only) -> IMU VDDIO + I2C pull-ups.
    v18 = Net("VDD_1V8")
    modem["VDD_EXT"] += v18
    imu["VDDIO"] += v18
    r_sda[1] += v18
    r_scl[1] += v18
    r_det[1] += v18
    r_dtr[1] += v18

    imuvdd = Net("IMU_VDD")
    ldo_imu["OUT"] += imuvdd
    ldo_imu["EN"] += vbat
    imu["VDD"] += imuvdd
    c_im1[1] += imuvdd
    c_im2[1] += imuvdd
    c_lo[1] += imuvdd

    sw_chg = Net("SW_CHG")          # buck switch node, L1 to the BAT node
    l_chg[1] += sw_chg
    charger["SW"] += sw_chg


    # --- I2C: 1K pull-ups to VDD_EXT (check list #9) ---------------
    sda = Net("SDA")
    modem["I2C_SDA"] += sda
    imu["SDA"] += sda
    r_sda[2] += sda
    fuel["SDA"] += sda

    scl = Net("SCL")
    modem["I2C_SCL"] += scl
    imu["SCL"] += scl
    r_scl[2] += scl
    fuel["SCL"] += scl

    # --- IMU interrupts -> GPIO2/GPIO3 ---------------------------
    # Deliberately NOT GPIO1: GPIO1 cannot be pulled up before boot,
    # and the IMU may drive INT high at power-up.
    int1 = Net("INT1")
    imu["INT1"] += int1
    r_i1[1] += int1
    int1m = Net("INT1_M")
    r_i1[2] += int1m
    modem["GPIO2"] += int1m

    int2 = Net("INT2")
    imu["INT2"] += int2
    r_i2[1] += int2
    int2m = Net("INT2_M")
    r_i2[2] += int2m
    modem["GPIO3"] += int2m

    # --- SIM: ONE net per line, all passing the ESDA6V1 pads -------
    # ESDA6V1-5SC6 is a 5-line SHUNT array (pins 1..5 = IO1..IO5,
    # pin 6 = GND) with NO feed-through path between IO pins. So each
    # line must be a single net joining module + TVS pad + holder; the
    # old *_H split nets would have left every SIM line electrically
    # OPEN. "Pass through the TVS pad first" (check list #8) is a
    # LAYOUT instruction, not a netlist split.
    # All 5 protected lines are used: CLK, DATA, RST, VSIM, DET.
    simclk = Net("SIM_CLK")
    modem["SIM_CLK"] += simclk
    esd_sim["IO1"] += simclk
    sim["CLK"] += simclk

    simdata = Net("SIM_DATA")
    modem["SIM_DATA"] += simdata
    esd_sim["IO2"] += simdata
    sim["I/O"] += simdata

    simrst = Net("SIM_RST")
    modem["SIM_RST"] += simrst
    esd_sim["IO3"] += simrst
    sim["RST"] += simrst

    vsim = Net("VSIM")   # 1.8V only on SIM7070G, no 3V legacy support
    modem["SIM_VDD"] += vsim
    esd_sim["IO4"] += vsim
    sim["VCC"] += vsim
    c_vs1[1] += vsim     # 100nF hard against the holder pins
    c_vs2[1] += vsim     # 22pF hard against the holder pins

    # Card detect: the SIM7070G has no SIM_DET pin, so the holder's
    # normally-open switch (SW shorts to GND on insert) pulls a GPIO
    # low; 10k pull-up to VDD_EXT holds it high when the card is out.
    simdet = Net("SIM_DET")
    sim["DET"] += simdet
    esd_sim["IO5"] += simdet
    r_det[2] += simdet
    modem["GPIO6"] += simdet

    # --- UART + USB debug/flash ----------------------------------
    txd = Net("UART1_TXD")
    modem["UART1_TXD"] += txd
    rxd = Net("UART1_RXD")
    modem["UART1_RXD"] += rxd
    dbgrx = Net("DEBUG_RXD")
    modem["DEBUG_RXD"] += dbgrx
    dbgtx = Net("DEBUG_TXD")
    modem["DEBUG_TXD"] += dbgtx
    dtr = Net("UART1_DTR")         # must be pulled up before sleep
    modem["UART1_DTR"] += dtr
    r_dtr[2] += dtr

    dp = Net("USB_DP")
    modem["USB_DP"] += dp
    esd_usb["I/O1"] += dp
    usb["D+"] += dp
    dm = Net("USB_DM")
    modem["USB_DM"] += dm
    esd_usb["I/O2"] += dm
    usb["D-"] += dm

    # --- Control straps ------------------------------------------
    pwrkey = Net("PWRKEY")         # active low; >12.6s = reset
    modem["PWRKEY"] += pwrkey
    boot = Net("BOOT_CFG")         # keep open before boot, TP + DNP jumper
    modem["BOOT_CFG"] += boot
    r_boot[1] += boot
    status = Net("STATUS")         # status LED output, TP only
    modem["STATUS"] += status

    # --- USB-C CC (USB2.0 sink: 5.1k each) -----------------------
    cc1 = Net("CC1")
    usb["CC1"] += cc1
    r_cc1[2] += cc1
    cc2 = Net("CC2")
    usb["CC2"] += cc2
    r_cc2[2] += cc2

    # --- RF PI networks ------------------------------------------
    # [RF_ANT pad] -> [shunt C12 DNP] -> [series R8 0R] -> [shunt C13 DNP]
    #   -> [50R microstrip] -> [U.FL J3]
    ant_lte = Net("ANT_LTE")
    modem["RF_ANT"] += ant_lte
    c_pilte_a[1] += ant_lte
    tvs_ant[1] += ant_lte
    lte_mid = Net("ANT_LTE_MID")
    r_pilte[1] += ant_lte
    r_pilte[2] += lte_mid
    c_pilte_b[1] += lte_mid
    ufl_lte["In"] += lte_mid

    ant_gnss = Net("ANT_GNSS")
    modem["GNSS_ANT"] += ant_gnss
    c_pignss_a[1] += ant_gnss
    gnss_mid = Net("ANT_GNSS_MID")
    r_pignss[1] += ant_gnss
    r_pignss[2] += gnss_mid
    c_pignss_b[1] += gnss_mid
    ufl_gnss["In"] += gnss_mid

    # --- Debug / flash test-point breakout -----------------------
    tp_pwrkey[1] += pwrkey
    tp_txd[1] += txd
    tp_rxd[1] += rxd
    tp_dbgtx[1] += dbgtx
    tp_dbgrx[1] += dbgrx
    tp_stat[1] += status
    tp_chg[1] += stat
    tp_vddext[1] += v18

