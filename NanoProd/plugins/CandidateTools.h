#pragma once

#include "DataFormats/PatCandidates/interface/PackedCandidate.h"

namespace cand_tools {
  inline const reco::Track* getTrack(const reco::Candidate& cand) {
    const reco::PFCandidate* pfCand = dynamic_cast<const reco::PFCandidate*>(&cand);
    if (pfCand != nullptr) {
      if (pfCand->trackRef().isNonnull())
        return &*pfCand->trackRef();
      else if (pfCand->gsfTrackRef().isNonnull())
        return &*pfCand->gsfTrackRef();
    }
    const pat::PackedCandidate* pCand = dynamic_cast<const pat::PackedCandidate*>(&cand);
    if (pCand != nullptr && pCand->hasTrackDetails())
      return &pCand->pseudoTrack();
    return nullptr;
  }
}  // namespace cand_tools

