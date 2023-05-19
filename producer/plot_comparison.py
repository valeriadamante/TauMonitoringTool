#import os, sys
import ROOT
ROOT.ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(True)

import argparse
from plotter_from_ntuplizer import obtain_histograms
from channel_to_HLT_map import channel_to_HLT_map


parser = argparse.ArgumentParser(description='Skim full tuple.')
parser.add_argument('--input_A', required=True, type=str, nargs='+', help="first input file")
parser.add_argument('--input_B', required=True, type=str, nargs='+', help="second input file")
parser.add_argument('--channel_A', required=True, type=str, 
       help="ditau, mutau, etau, VBFasymtau_uppertauleg, VBFasymtau_lowertauleg, ditaujet_tauleg, ditaujet_jetleg, VBFditau_old,\
       or VBFditau_Run3_tauleg")
parser.add_argument('--channel_B', required=True, type=str, 
       help="ditau, mutau, etau, VBFasymtau_uppertauleg, VBFasymtau_lowertauleg, ditaujet_tauleg, ditaujet_jetleg, VBFditau_old,\
       or VBFditau_Run3_tauleg")
parser.add_argument('--run', required=True, type=str, help="runs or fill used (look at your input files)")
parser.add_argument('--plot', required=True, type=str, help="plot name")
parser.add_argument('--iseta', action='store_true', help="sets flag for eat plotting")
parser.add_argument('--var', required=True, type=str, help="tau_pt, tau_eta, jet_pt, jet_eta")


# FIXME: possible channels should be defined in one location and imported where needed
#        same for help statement of channel arguments in argparse
possibleChannels = ["ditau", "mutau", "etau", \
                    "VBFasymtau_uppertauleg", "VBFasymtau_lowertauleg", \
                    "ditaujet_tauleg", "ditaujet_jetleg",\
                    "VBFditau_old", "VBFditau_Run3_tauleg"]

def plot_comparison(h_num_os, h_den_os, plottingVariable, channels, add_to_label, plotName, legends=["v2p1", "v2p5"]):

    assert len(channels) == 1 or len(channels) == len(h_num_os)
    assert len(h_num_os) == len(legends)
    channels = channels if not all([elem == channels[0] for elem in channels]) else [channels[0]]

    print("Plotting {} of {}".format(plottingVariable, ", ".join(channels)))

    ROOT.gStyle.SetOptStat(0); ROOT.gStyle.SetTextFont(42)
    c = ROOT.TCanvas("c", "", 800, 700)

    # use multiplotter for multiple graphs
    mg = ROOT.TMultiGraph("mg", "")

    # this divides num by den.
    # the "Clopper-Pearson" interval is not supported for
    # TGraphAsymmErrors::Divide, so i changed "cp" to "n"
    # the graphs are not changed
    # https://root.cern.ch/doc/master/classTGraphAsymmErrors.html#a37a202762b286cf4c7f5d34046be8c0b
    # use "nv" to get per-bin efficiency printed to terminal

    # add legend
    leg = ROOT.TLegend(0.55, 0.15, 0.90, 0.15 + 0.05 * len(legends))

    histos = []
    iplot = 0
    for (h_num_os_A, h_den_os_A, legend) in zip(h_num_os, h_den_os, legends):
        if iplot == 3:
            iplot += 1
        gr_A = ROOT.TGraphAsymmErrors(h_num_os_A.GetPtr(), h_den_os_A.GetPtr(), "n")
        gr_A.SetTitle("")
        gr_A.SetLineColor(2 + 1 * iplot) # this is red
        gr_A.SetMarkerColor(2 + 1 * iplot) # this is red
        #gr_A.SetMarkerColor(2 + 2 * iplot) # this is red
        gr_A.SetMarkerStyle(24 + iplot) # this is a filled box
        gr_A.SetMarkerSize(1.5)
        histos.append(gr_A)
        mg.Add(histos[-1])
        leg.AddEntry(histos[-1], legend)
        iplot += 1
    leg.Draw()

    # "P" forces the use of the chosen marker
    # "A" draws without the axis 
    # somehow the plot is not drawn without this argument
    # https://root.cern/doc/master/classTHistPainter.html#HP01a
    mg.Draw("AP")

    label = ROOT.TLatex(); label.SetNDC(True)
    if(plottingVariable == "tau_pt" or plottingVariable=="tau_l1pt"):
        label.DrawLatex(0.8, 0.03, "p_{T}^{#tau}") ##tau_{pT}")
    elif(plottingVariable == "jet_pt"):
        label.DrawLatex(0.8, 0.03, "p_{T}^{jet}") #jet_{pT}")
    elif(plottingVariable == "jet_eta"):
        label.DrawLatex(0.8, 0.03, "#eta_{jet}")
    else:
        label.DrawLatex(0.8, 0.03, "#eta_{#tau}")

    label.SetTextSize(0.040)
    label.DrawLatex(0.100, 0.920, "#bf{CMS Run3 Data}")
    
    label.SetTextSize(0.030) 
    label.SetTextAlign(31)
    label.DrawLatex(0.9, 0.920, "#sqrt{s} = 13.6 TeV, %s" % add_to_label)


    # leg.SetTextSize(0.045)

    leg.Draw()

    combined_name = "_".join(channels)
    c.SaveAs("%s_%s_%s.pdf" % (plotName, combined_name, plottingVariable))
    c.SaveAs("%s_%s_%s.png" % (plotName, combined_name, plottingVariable))

    tf = ROOT.TFile.Open("%s_%s_%s.root" % (plotName, combined_name, plottingVariable), "RECREATE")
    for histo, legend in zip(histos, legends):
        histo.Write(legend.replace(" ", "_"))
    tf.Close()


if __name__ == "__main__":

    args = parser.parse_args()
    channel_A = args.channel_A
    channel_B = args.channel_B
    plottingVariable = args.var
    iseta = "eta" in "plottingVariable"
    print(args.input_A, args.input_B)
    df_A = ROOT.RDataFrame("Events",tuple(args.input_A))
    h_num_os_A, h_den_os_A = obtain_histograms(df_A, channel_A, iseta, plottingVariable)
    df_B = ROOT.RDataFrame("Events",tuple(args.input_B))
    h_num_os_B, h_den_os_B = obtain_histograms(df_B, channel_B, iseta, plottingVariable)

    plot_comparison(h_num_os_A, h_den_os_A, h_num_os_B, h_den_os_B, plottingVariable, channel_A, channel_B, args.run, args.plot)
