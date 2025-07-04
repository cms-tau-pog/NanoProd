

selection = """
  const auto ele_base_sel = Electron_pt > 5 && (abs(Electron_eta) < 2.5 || abs(Electron_eta+Electron_deltaEtaSC) < 2.5);
  const auto ele_isoId_sel = Electron_mvaIso_WP90;
  const auto ele_noIsoId_sel = Electron_mvaNoIso_WP90 || Electron_cutBased >= 2;
  const auto ele_highPtId_sel = Electron_pt > 35 && Electron_cutBased_HEEP;
  const auto ele_pfIso_sel = Electron_pfRelIso03_all < 0.5 || Electron_miniPFRelIso_all < 0.5;
  const auto ele_sel = ele_base_sel && (ele_isoId_sel || (ele_noIsoId_sel && ele_pfIso_sel) || ele_highPtId_sel);

  const auto muon_base_sel = Muon_pt > 5 && abs(Muon_eta) < 2.4;
  const auto muon_id_sel = Muon_tightId || Muon_mediumId || Muon_mediumPromptId || Muon_highPtId || Muon_mvaMuID_WP >= 1 || Muon_miniIsoId >= 2;
  const auto muon_iso_sel = Muon_pfRelIso04_all < 0.5 || Muon_pfRelIso03_all < 0.5 || Muon_tkRelIso < 0.5 || Muon_miniPFRelIso_all < 0.5;
  const auto muon_sel = muon_base_sel && muon_id_sel && muon_iso_sel;

  const auto tau_base_sel = Tau_pt > 18 && abs(Tau_eta) < 2.5;
  const auto tau_deepTau_v2p1_sel = Tau_rawDeepTau2017v2p1VSmu > 0.05 && Tau_idDeepTau2017v2p1VSjet > 0 && Tau_idDeepTau2017v2p1VSe > 0;
  const auto tau_deepTau_v2p5_sel = Tau_rawDeepTau2018v2p5VSmu > 0.05 && Tau_idDeepTau2018v2p5VSjet > 0 && Tau_idDeepTau2018v2p5VSe > 0;
  const auto tau_deepTau_v2p5noDA_sel = Tau_rawDeepTau2018v2p5noDAVSmu > 0.05 && Tau_idDeepTau2018v2p5noDAVSjet > 0 && Tau_idDeepTau2018v2p5noDAVSe > 0;
  const auto tau_pnet_sel = Tau_rawPNetVSjet > 0.05 && Tau_rawPNetVSe > 0.05 && Tau_rawPNetVSmu > 0.05;
  const auto tau_sel = tau_base_sel && (tau_deepTau_v2p1_sel || tau_deepTau_v2p5_sel || tau_deepTau_v2p5noDA_sel || tau_pnet_sel);

  const size_t n_electrons = Sum(ele_sel);
  const size_t n_muons = Sum(muon_sel);
  const size_t n_taus = Sum(tau_sel);
  const size_t n_leptons = n_electrons + n_muons + n_taus;

  // Accept di-lepton events
  if (n_leptons >= 2) return true;

  using LorentzVectorM = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>;
  LorentzVectorM lep_p4(0, 0, 0, 0);
  if(n_electrons > 0)
    lep_p4 = LorentzVectorM(Electron_pt[ele_sel].at(0), Electron_eta[ele_sel].at(0), Electron_phi[ele_sel].at(0), Electron_mass[ele_sel].at(0));
  if(n_muons > 0)
    lep_p4 = LorentzVectorM(Muon_pt[muon_sel].at(0), Muon_eta[muon_sel].at(0), Muon_phi[muon_sel].at(0), Muon_mass[muon_sel].at(0));
  if(n_taus > 0)
    lep_p4 = LorentzVectorM(Tau_pt[tau_sel].at(0), Tau_eta[tau_sel].at(0), Tau_phi[tau_sel].at(0), Tau_mass[tau_sel].at(0));

  // lepton + MET
  if(n_leptons > 0) {
    static constexpr int met_cut = 100;
    const bool has_high_met = PFMET_pt > met_cut || DeepMETResolutionTune_pt > met_cut || DeepMETResponseTune_pt > met_cut || PuppiMET_pt > met_cut;
    const float lep_pt_thr = n_electrons > 0 ? 28.0 : (n_muons > 0 ? 20.0 : 120);
    if(lep_p4.pt() > lep_pt_thr || has_high_met) return true;
  }

  // High-HT selection
  const float HT = Sum(Jet_pt);
  if(HT > 400) return true;

  ROOT::VecOps::RVec<LorentzVectorM> Jet_p4(nJet);
  for(int i = 0; i < nJet; ++i)
    Jet_p4[i] = LorentzVectorM(Jet_pt[i], Jet_eta[i], Jet_phi[i], Jet_mass[i]);

  // VBF selection
  static constexpr float vbf_delta_eta_cut = 3.0;
  float max_m_jj = 0;
  for(int i = 0; i < nJet; ++i) {
    for(int j = i + 1; j < nJet; ++j) {
      const float m_jj = (Jet_p4[i] + Jet_p4[j]).mass();
      const float delta_eta = abs(Jet_eta[i] - Jet_eta[j]);
      if(m_jj > max_m_jj && delta_eta > vbf_delta_eta_cut) {
        max_m_jj = m_jj;
      }
    }
  }
  if(max_m_jj > 800) return true;

  // 4j2b selection
  const auto bjet_sel = Jet_pt > 25 && abs(Jet_eta) < 2.5;
  auto btag_scores = Jet_btagPNetB[bjet_sel];
  std::sort(btag_scores.begin(), btag_scores.end(), std::greater<float>());
  if(btag_scores.size() >= 4 && (btag_scores[0] + btag_scores[1]) / 2. > 0.5) return true;

  // Boosted selection
  if(nFatJet >= 2) return true;
  if(nFatJet > 0) {
    static constexpr float deltaR2_cut = 0.8*0.8;
    LorentzVectorM fatJet_p4(FatJet_pt[0], FatJet_eta[0], FatJet_phi[0], FatJet_mass[0]);
    if(n_leptons > 0 && ROOT::Math::VectorUtil::DeltaR2(fatJet_p4, lep_p4) > deltaR2_cut) return true;
    size_t n_other_jets = 0;
    for(const auto& jet_p4 : Jet_p4[bjet_sel]) {
      if(ROOT::Math::VectorUtil::DeltaR2(fatJet_p4, jet_p4) > deltaR2_cut)
        ++n_other_jets;
    }
    if(n_other_jets >= 2) return true;
  }

  // Boosted taus selection (in case the seeding AK8 jet did not pass the miniAOD/nanoAOD selection)
  auto boostedtau_base_sel = boostedTau_pt > 18 && abs(boostedTau_eta) < 2.5;
  auto boostedtau_deepTau_sel = boostedTau_rawBoostedDeepTauRunIIv2p0VSjet > 0.72 && boostedTau_rawBoostedDeepTauRunIIv2p0VSe > 0.1 && boostedTau_rawBoostedDeepTauRunIIv2p0VSmu > 0.003;
  auto boostedtau_sel = boostedtau_base_sel && boostedtau_deepTau_sel;

  ROOT::VecOps::RVec<LorentzVectorM> boostedTau_p4(nboostedTau);
  for(int i = 0; i < nboostedTau; ++i)
    boostedTau_p4[i] = LorentzVectorM(boostedTau_pt[i], boostedTau_eta[i], boostedTau_phi[i], boostedTau_mass[i]);
  const auto selected_boosteTau_p4 = boostedTau_p4[boostedtau_sel];
  const size_t n_boostedtaus = selected_boosteTau_p4.size();

  const auto pass_boosted_dR = [&](const LorentzVectorM& a_p4, const LorentzVectorM& b_p4) {
    static constexpr float maxR2 = 0.8*0.8;
    static constexpr float minR2 = 0.01*0.01;
    const float dr2 = ROOT::Math::VectorUtil::DeltaR2(a_p4[i], b_p4[j]);
    return dr2 > minR2 && dr2 < maxR2;
  };

  if(n_boostedtaus >= 2) {
    for(size_t i = 0; i < selected_boosteTau_p4.size() - 1; ++i) {
      for(size_t j = i + 1; j < selected_boosteTau_p4.size(); ++j) {
        if(pass_boosted_dR(selected_boosteTau_p4[i], selected_boosteTau_p4[j]))
          return true;
      }
    }
  }
  if(n_boostedtaus > 0 && n_leptons > 0) {
    for(size_t i = 0; i < selected_boosteTau_p4.size(); ++i) {
      if(pass_boosted_dR(selected_boosteTau_p4[i], lep_p4))
        return true;
    }
  }

  // No selection criteria matched
  return false;
"""

def skim(df):
  return df.Filter(selection)

def skim_failed(df):
  return df.Define('__passSkimSel', selection).Filter('!__passSkimSel')

def select_ll(df, lep_pdgId):
  return df.Filter(f'Sum(abs(LHEPart_pdgId) == {lep_pdgId}) == 2')

def skim_ll(df, lep_pdgId):
  df = select_ll(df, lep_pdgId)
  return skim(df)

def skim_ll_failed(df, lep_pdgId):
  df = select_ll(df, lep_pdgId)
  return skim_failed(df)

def skim_ee(df):
  return skim_ll(df, 11)

def skim_ee_failed(df):
  return skim_ll_failed(df, 11)

def skim_mumu(df):
  return skim_ll(df, 13)

def skim_mumu_failed(df):
  return skim_ll_failed(df, 13)

def skim_tautau(df):
  return skim_ll(df, 15)

def skim_tautau_failed(df):
  return skim_ll_failed(df, 15)