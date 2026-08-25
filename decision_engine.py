# decision_engine.py
# Deterministic Signal Ranker and Decision Engine

from typing import Dict, Any, List

class Decision:
    def __init__(self, primary_signal: str, supporting_fact: str, recommended_action: str, urgency_hook: str = ""):
        self.primary_signal = primary_signal
        self.supporting_fact = supporting_fact
        self.recommended_action = recommended_action
        self.urgency_hook = urgency_hook  # loss-aversion / time-pressure hook

    def __repr__(self):
        return f"<Decision signal='{self.primary_signal}' fact='{self.supporting_fact}' action='{self.recommended_action}'>"


def evaluate_signals(
    merchant_context: Dict[str, Any],
    trigger_context: Dict[str, Any],
    category_context: Dict[str, Any]
) -> Decision:
    """
    Deterministically evaluates the merchant state and trigger to decide
    exactly what the LLM should focus on, enforcing Specificity and Decision Quality.
    """
    trigger_kind = trigger_context.get("kind", "")
    trigger_payload = trigger_context.get("payload", {})
    trigger_urgency = trigger_context.get("urgency", 1)
    
    perf = merchant_context.get("performance", {})
    views = perf.get("views", 0)
    calls = perf.get("calls", 0)
    ctr = perf.get("ctr", "0%")
    
    offers = merchant_context.get("offers", [])
    active_offers = [o.get("title", "") for o in offers if o.get("status") == "active"]
    
    # Category peer stats for comparison
    peer_stats = category_context.get("peer_stats", {})
    avg_views = peer_stats.get("avg_views_30d", 0)
    avg_calls = peer_stats.get("avg_calls_30d", 0)
    
    merchant_name = merchant_context.get("identity", {}).get("name", "your business")
    owner_name = merchant_context.get("identity", {}).get("owner_first_name", "Partner")
    locality = merchant_context.get("identity", {}).get("locality", "your area")
    
    primary_signal = ""
    supporting_fact = ""
    recommended_action = ""
    urgency_hook = ""
    
    # ---------------------------------------------------------
    # RESEARCH DIGEST
    # ---------------------------------------------------------
    if trigger_kind == "research_digest":
        cat = trigger_payload.get("category", "")
        top_item_id = trigger_payload.get("top_item_id", "")
        # Find the digest item from category context
        digest_items = category_context.get("digest", [])
        digest_item = next((d for d in digest_items if d.get("id") == top_item_id), None)
        
        if digest_item:
            source = digest_item.get("source", "industry research")
            title = digest_item.get("title", "new insight")
            summary = digest_item.get("summary", "")
            actionable = digest_item.get("actionable", "")
            trial_n = digest_item.get("trial_n", "")
            
            primary_signal = f"New finding: {title}. Source: {source}."
            if trial_n:
                primary_signal += f" Study sample: {trial_n} patients."
            supporting_fact = f"{summary[:150]}. Actionable: {actionable}"
            recommended_action = f"Share this insight and ask if they want to act on it. Ask exactly: 'Want me to flag the relevant patients in your records for this?'"
            urgency_hook = "This finding is time-sensitive — acting early gives a competitive edge."
        else:
            source = trigger_context.get("source", "industry research")
            primary_signal = f"New insight from {source} indicates a rising trend."
            supporting_fact = "Updating your practice to match this trend could increase your visibility."
            recommended_action = "Ask exactly: 'Would you like me to update your profile to capture this trend?'"
            urgency_hook = "Early movers capture the most traffic from new trends."

    # ---------------------------------------------------------
    # REGULATION CHANGE
    # ---------------------------------------------------------
    elif trigger_kind == "regulation_change":
        top_item_id = trigger_payload.get("top_item_id", "")
        deadline = trigger_payload.get("deadline_iso", "")
        digest_items = category_context.get("digest", [])
        digest_item = next((d for d in digest_items if d.get("id") == top_item_id), None)
        
        if digest_item:
            title = digest_item.get("title", "regulatory update")
            source = digest_item.get("source", "")
            summary = digest_item.get("summary", "")
            actionable = digest_item.get("actionable", "")
            primary_signal = f"Regulatory update: {title}. Deadline: {deadline}. Source: {source}."
            supporting_fact = f"{summary[:150]}. Action needed: {actionable}"
            recommended_action = f"Alert them about the deadline and offer help. Ask exactly: 'Need help auditing your setup before the {deadline} deadline?'"
            urgency_hook = f"Non-compliance after {deadline} risks penalties."
        else:
            primary_signal = f"A new regulation takes effect on {deadline}."
            supporting_fact = "Compliance is required before the deadline."
            recommended_action = f"Ask exactly: 'Want me to help you prepare before the {deadline} deadline?'"
            urgency_hook = "Missing regulatory deadlines can result in fines."

    # ---------------------------------------------------------
    # PERF DIP / ENGAGEMENT DROP
    # ---------------------------------------------------------
    elif trigger_kind in ["perf_dip", "engagement_drop"]:
        metric = trigger_payload.get("metric", "engagement")
        delta = trigger_payload.get("delta_pct", 0)
        window = trigger_payload.get("window", "7d")
        vs_baseline = trigger_payload.get("vs_baseline", 0)
        
        delta_display = f"{abs(delta * 100):.0f}%" if abs(delta) < 1 else f"{abs(delta)}%"
        
        primary_signal = f"Your {metric} dropped {delta_display} in the last {window}. Current {metric}: {vs_baseline if vs_baseline else calls}, vs category avg: {avg_calls if metric == 'calls' else avg_views}."
        
        if not active_offers:
            supporting_fact = f"You have 0 active offers while competitors in {locality} are running promotions."
            recommended_action = f"Ask exactly: 'Should we create a targeted offer to recover these lost {metric}?'"
        else:
            supporting_fact = f"Your '{active_offers[0]}' offer is active but {metric} are still declining."
            recommended_action = f"Ask exactly: 'Should we boost your {active_offers[0]} offer to stop this decline?'"
        urgency_hook = f"Every day without action means more lost {metric}."

    # ---------------------------------------------------------
    # PERF SPIKE
    # ---------------------------------------------------------
    elif trigger_kind == "perf_spike":
        metric = trigger_payload.get("metric", "engagement")
        delta = trigger_payload.get("delta_pct", 0)
        window = trigger_payload.get("window", "7d")
        vs_baseline = trigger_payload.get("vs_baseline", 0)
        driver = trigger_payload.get("likely_driver", "recent activity")
        
        delta_display = f"{abs(delta * 100):.0f}%" if abs(delta) < 1 else f"{abs(delta)}%"
        
        primary_signal = f"Your {metric} surged {delta_display} in the last {window}, likely driven by {driver}. Current: {vs_baseline if vs_baseline else calls} (category avg: {avg_calls if metric == 'calls' else avg_views})."
        
        if active_offers:
            supporting_fact = f"Your '{active_offers[0]}' offer is live — perfect time to amplify."
            recommended_action = f"Ask exactly: 'Want to boost {active_offers[0]} while this momentum lasts?'"
        else:
            supporting_fact = f"You have 0 active offers to capture this surge."
            recommended_action = "Ask exactly: 'Should we launch a quick offer to convert this extra traffic?'"
        urgency_hook = "Traffic spikes are temporary — capturing them now maximizes ROI."

    # ---------------------------------------------------------
    # SEASONAL PERF DIP
    # ---------------------------------------------------------
    elif trigger_kind == "seasonal_perf_dip":
        metric = trigger_payload.get("metric", "views")
        delta = trigger_payload.get("delta_pct", 0)
        season_note = trigger_payload.get("season_note", "seasonal trend")
        is_expected = trigger_payload.get("is_expected_seasonal", False)
        
        delta_display = f"{abs(delta * 100):.0f}%" if abs(delta) < 1 else f"{abs(delta)}%"
        
        primary_signal = f"Your {metric} dipped {delta_display} — this is {'expected' if is_expected else 'unusual'} for this season ({season_note.replace('_', ' ')})."
        supporting_fact = f"Category avg {metric}: {avg_views if metric == 'views' else avg_calls}. Focus should shift to retention over acquisition."
        recommended_action = "Ask exactly: 'Should we shift focus to retaining your current members instead of acquiring new ones?'"
        urgency_hook = "Smart operators use slow seasons to strengthen retention — competitors are sleeping."

    # ---------------------------------------------------------
    # REVIEW BOOST / MILESTONE
    # ---------------------------------------------------------
    elif trigger_kind in ["review_boost", "milestone_reached"]:
        if trigger_kind == "milestone_reached":
            metric_name = trigger_payload.get("metric", "reviews")
            value_now = trigger_payload.get("value_now", 0)
            milestone = trigger_payload.get("milestone_value", 0)
            is_imminent = trigger_payload.get("is_imminent", False)
            gap = milestone - value_now
            
            primary_signal = f"You're at {value_now} {metric_name} — just {gap} away from the {milestone} milestone!"
            supporting_fact = f"Hitting {milestone} {metric_name} unlocks higher search ranking and trust signals for customers in {locality}."
            recommended_action = f"Ask exactly: 'Should we send a quick review request to your recent customers to hit {milestone}?'"
            urgency_hook = f"You're only {gap} away — this could happen this week."
        else:
            current = trigger_payload.get("current_reviews", 0)
            target = trigger_payload.get("target_reviews", 0)
            rating = trigger_payload.get("avg_rating", 0)
            primary_signal = f"You have {current} reviews (rating: {rating}★) — {target - current} away from {target}."
            supporting_fact = f"Category avg is {peer_stats.get('avg_review_count', 0)} reviews. You're {'ahead' if current > peer_stats.get('avg_review_count', 0) else 'behind'}."
            recommended_action = f"Ask exactly: 'Should we send a review request to recent customers to reach {target}?'"
            urgency_hook = f"Just {target - current} more reviews to cross the milestone."

    # ---------------------------------------------------------
    # IPL MATCH TODAY
    # ---------------------------------------------------------
    elif trigger_kind == "ipl_match_today":
        match = trigger_payload.get("match", "")
        venue = trigger_payload.get("venue", "")
        match_time = trigger_payload.get("match_time_iso", "")
        is_weeknight = trigger_payload.get("is_weeknight", False)
        
        primary_signal = f"IPL match today: {match} at {venue}. {'Weeknight matches drive +18% covers' if is_weeknight else 'Weekend matches shift traffic to home-watch parties'}."
        supporting_fact = f"Category data shows match-night combos on {'weeknights drive max footfall' if is_weeknight else 'weekends need aggressive push to compete with home viewing'}."
        recommended_action = "Ask exactly: 'Want to activate a match-night combo offer for tonight?'"
        urgency_hook = "Match starts soon — activating now captures the pre-match crowd."

    # ---------------------------------------------------------
    # REVIEW THEME EMERGED
    # ---------------------------------------------------------
    elif trigger_kind == "review_theme_emerged":
        theme = trigger_payload.get("theme", "issue").replace("_", " ")
        occurrences = trigger_payload.get("occurrences_30d", 0)
        trend = trigger_payload.get("trend", "stable")
        quote = trigger_payload.get("common_quote", "")
        
        primary_signal = f"Review pattern detected: '{theme}' mentioned {occurrences} times in the last 30 days (trend: {trend})."
        supporting_fact = f"A customer wrote: \"{quote}\". This is affecting your reputation in {locality}."
        recommended_action = f"Ask exactly: 'Should we address this {theme} pattern before it affects more reviews?'"
        urgency_hook = f"This theme is {trend} — addressing it now prevents further damage."

    # ---------------------------------------------------------
    # FESTIVAL UPCOMING
    # ---------------------------------------------------------
    elif trigger_kind == "festival_upcoming":
        festival = trigger_payload.get("festival", "festival")
        days_until = trigger_payload.get("days_until", 0)
        
        primary_signal = f"{festival} is {days_until} days away."
        supporting_fact = f"Festival seasons drive 2-4x bookings in your category. Early preparation captures the most business in {locality}."
        recommended_action = f"Ask exactly: 'Should we start planning your {festival} promotion now to get ahead?'"
        urgency_hook = f"Competitors in {locality} are already preparing — early movers win."

    # ---------------------------------------------------------
    # COMPETITOR OPENED
    # ---------------------------------------------------------
    elif trigger_kind == "competitor_opened":
        comp_name = trigger_payload.get("competitor_name", "a competitor")
        distance = trigger_payload.get("distance_km", 0)
        their_offer = trigger_payload.get("their_offer", "")
        
        primary_signal = f"New competitor '{comp_name}' opened {distance}km away, offering '{their_offer}'."
        if active_offers:
            supporting_fact = f"Your active offer '{active_offers[0]}' needs to stand out against theirs."
        else:
            supporting_fact = f"You have 0 active offers while they're running '{their_offer}'."
        recommended_action = f"Ask exactly: 'Should we create a competitive offer to protect your {locality} customers?'"
        urgency_hook = f"They're {distance}km away and already attracting your potential patients."

    # ---------------------------------------------------------
    # CDE OPPORTUNITY
    # ---------------------------------------------------------
    elif trigger_kind == "cde_opportunity":
        digest_id = trigger_payload.get("digest_item_id", "")
        credits = trigger_payload.get("credits", 0)
        fee = trigger_payload.get("fee", "")
        digest_items = category_context.get("digest", [])
        digest_item = next((d for d in digest_items if d.get("id") == digest_id), None)
        
        if digest_item:
            title = digest_item.get("title", "training opportunity")
            source = digest_item.get("source", "")
            primary_signal = f"CDE opportunity: {title}. {credits} credits. Fee: {fee}. Source: {source}."
            supporting_fact = digest_item.get("summary", "")
            recommended_action = f"Ask exactly: 'Want me to register you for this {credits}-credit session?'"
            urgency_hook = "Spots fill up fast — registering early secures your place."
        else:
            primary_signal = f"A continuing education opportunity with {credits} credits is available."
            supporting_fact = f"Fee: {fee}."
            recommended_action = f"Ask exactly: 'Want me to register you for this session?'"
            urgency_hook = "Limited spots available."

    # ---------------------------------------------------------
    # WINBACK / DORMANCY
    # ---------------------------------------------------------
    elif trigger_kind in ["winback_eligible", "dormant_with_vera"]:
        if trigger_kind == "winback_eligible":
            days = trigger_payload.get("days_since_expiry", 0)
            dip = trigger_payload.get("perf_dip_pct", 0)
            lapsed = trigger_payload.get("lapsed_customers_added_since_expiry", 0)
            dip_display = f"{abs(dip * 100):.0f}%" if abs(dip) < 1 else f"{abs(dip)}%"
            
            primary_signal = f"Your plan expired {days} days ago. Performance dropped {dip_display} since then, and {lapsed} potential customers were added but not engaged."
            supporting_fact = f"Those {lapsed} customers in {locality} are waiting to be reached."
            recommended_action = f"Ask exactly: 'Should we reactivate your plan to reach those {lapsed} waiting customers?'"
            urgency_hook = f"{lapsed} customers are drifting to competitors every day you wait."
        else:
            days = trigger_payload.get("days_since_last_merchant_message", 0)
            last_topic = trigger_payload.get("last_topic", "").replace("_", " ")
            primary_signal = f"It's been {days} days since your last interaction. Last topic: {last_topic}."
            supporting_fact = f"Your profile has had {views} views and {calls} calls — customers are still finding you in {locality}."
            recommended_action = f"Ask exactly: 'Should we pick up where we left off on {last_topic}?'"
            urgency_hook = f"Your competitors in {locality} are actively engaging — staying silent costs you."

    # ---------------------------------------------------------
    # CURIOUS ASK DUE
    # ---------------------------------------------------------
    elif trigger_kind == "curious_ask_due":
        ask_template = trigger_payload.get("ask_template", "").replace("_", " ")
        primary_signal = f"It's time for a check-in: {ask_template}."
        supporting_fact = f"Your profile has {views} views and {calls} calls this month in {locality}."
        recommended_action = f"Ask exactly: 'Quick question — what service has been most popular for you this week?'"
        urgency_hook = "Understanding your top service helps us target the right customers."

    # ---------------------------------------------------------
    # ACTIVE PLANNING INTENT
    # ---------------------------------------------------------
    elif trigger_kind == "active_planning_intent":
        topic = trigger_payload.get("intent_topic", "").replace("_", " ")
        last_msg = trigger_payload.get("merchant_last_message", "")
        primary_signal = f"Merchant is actively planning: {topic}. They said: '{last_msg}'"
        supporting_fact = f"This is a high-intent moment — they're ready to act."
        recommended_action = f"Provide a concrete next step for {topic}. Ask exactly: 'I have a draft ready — should I share it with you now?'"
        urgency_hook = "They're ready NOW — delayed response risks losing this momentum."

    # ---------------------------------------------------------
    # SUPPLY ALERT
    # ---------------------------------------------------------
    elif trigger_kind == "supply_alert":
        molecule = trigger_payload.get("molecule", "medication")
        batches = trigger_payload.get("affected_batches", [])
        manufacturer = trigger_payload.get("manufacturer", "")
        
        primary_signal = f"Recall alert: {molecule} batches {', '.join(batches)} from {manufacturer} flagged for issues."
        supporting_fact = "Affected customers need to be notified and replacements arranged."
        recommended_action = f"Ask exactly: 'Should I help you identify affected customers and arrange replacements?'"
        urgency_hook = "Patient safety is at stake — immediate action is critical."

    # ---------------------------------------------------------
    # CATEGORY SEASONAL
    # ---------------------------------------------------------
    elif trigger_kind == "category_seasonal":
        season = trigger_payload.get("season", "").replace("_", " ")
        trends = trigger_payload.get("trends", [])
        trends_text = ", ".join([t.replace("_", " ") for t in trends[:3]])
        
        primary_signal = f"Seasonal shift ({season}): {trends_text}."
        supporting_fact = f"Rearranging your shelf and promotions to match demand increases revenue."
        recommended_action = "Ask exactly: 'Should we update your promotions to match the seasonal demand shift?'"
        urgency_hook = "Seasonal demand is already shifting — early adjustment captures the most sales."

    # ---------------------------------------------------------
    # GBP UNVERIFIED
    # ---------------------------------------------------------
    elif trigger_kind == "gbp_unverified":
        uplift = trigger_payload.get("estimated_uplift_pct", 0)
        uplift_display = f"{abs(uplift * 100):.0f}%" if abs(uplift) < 1 else f"{abs(uplift)}%"
        verification_path = trigger_payload.get("verification_path", "postcard or phone call")
        
        primary_signal = f"Your Google Business Profile is unverified. Verified profiles get ~{uplift_display} more visibility."
        supporting_fact = f"Verification is free via {verification_path.replace('_', ' ')}. Your competitors in {locality} are likely verified."
        recommended_action = f"Ask exactly: 'Should I guide you through the {verification_path.replace('_', ' ')} verification process?'"
        urgency_hook = f"You're missing out on {uplift_display} more customers every day."

    # ---------------------------------------------------------
    # CUSTOMER-FACING: recall, renewal, reorder, winback, appointment
    # ---------------------------------------------------------
    elif trigger_kind in ["recall_due", "renewal_due", "reorder_reminder", "winback", "appointment_reminder",
                          "customer_lapsed_hard", "chronic_refill_due", "wedding_package_followup", "trial_followup"]:
        service = (
            trigger_payload.get("service") or 
            trigger_payload.get("service_due") or
            trigger_payload.get("medicine") or 
            trigger_payload.get("plan") or 
            trigger_payload.get("favorite_item") or
            trigger_payload.get("previous_focus") or
            "service"
        )
        
        if trigger_kind == "recall_due":
            due_date = trigger_payload.get("due_date", "")
            slots = trigger_payload.get("available_slots", [])
            slot_labels = [s.get("label", "") for s in slots[:2]]
            primary_signal = f"Their {service.replace('_', ' ')} is due on {due_date}."
            supporting_fact = f"Available slots: {', '.join(slot_labels) if slot_labels else 'flexible scheduling'}."
            recommended_action = f"Ask exactly: 'Your {service.replace('_', ' ')} is due — would {slot_labels[0] if slot_labels else 'this week'} work for you?'"
            urgency_hook = "Booking now ensures they get their preferred time slot."
            
        elif trigger_kind == "chronic_refill_due":
            molecules = trigger_payload.get("molecule_list", [])
            stock_runs_out = trigger_payload.get("stock_runs_out_iso", "")
            delivery_saved = trigger_payload.get("delivery_address_saved", False)
            
            primary_signal = f"Their medication ({', '.join(molecules)}) stock runs out around {stock_runs_out[:10]}."
            supporting_fact = f"Delivery address is {'saved' if delivery_saved else 'not saved'}. Molecules: {', '.join(molecules)}."
            recommended_action = f"Ask exactly: 'Your {molecules[0] if molecules else 'medication'} refill is due — should we deliver to your saved address?'"
            urgency_hook = "Running out of chronic medication risks health complications."
            
        elif trigger_kind == "wedding_package_followup":
            wedding_date = trigger_payload.get("wedding_date", "")
            days_to_wedding = trigger_payload.get("days_to_wedding", 0)
            next_step = trigger_payload.get("next_step_window_open", "").replace("_", " ")
            
            primary_signal = f"Wedding is {days_to_wedding} days away ({wedding_date}). Next step: {next_step}."
            supporting_fact = f"Trial was completed — now is the window for {next_step}."
            recommended_action = f"Ask exactly: 'Your wedding is {days_to_wedding} days away — should we start the {next_step} now?'"
            urgency_hook = f"Starting {next_step} now ensures best results by the wedding date."
            
        elif trigger_kind == "trial_followup":
            trial_date = trigger_payload.get("trial_date", "")
            sessions = trigger_payload.get("next_session_options", [])
            session_labels = [s.get("label", "") for s in sessions[:2]]
            
            primary_signal = f"They completed a trial on {trial_date}."
            supporting_fact = f"Next available sessions: {', '.join(session_labels) if session_labels else 'flexible'}."
            recommended_action = f"Ask exactly: 'Enjoyed your trial? Would {session_labels[0] if session_labels else 'next week'} work for your next session?'"
            urgency_hook = "Converting trials within 7 days has the highest success rate."
            
        elif trigger_kind == "customer_lapsed_hard":
            days = trigger_payload.get("days_since_last_visit", 0)
            previous_focus = trigger_payload.get("previous_focus", "fitness").replace("_", " ")
            prev_months = trigger_payload.get("previous_membership_months", 0)
            
            primary_signal = f"They haven't visited in {days} days. Previous focus: {previous_focus}. Was a member for {prev_months} months."
            supporting_fact = f"They invested {prev_months} months in {previous_focus} — that progress is at risk."
            recommended_action = f"Ask exactly: 'You put in {prev_months} months of work on {previous_focus} — should we help you get back on track?'"
            urgency_hook = f"After {days} days, fitness gains start reversing — acting now preserves their progress."
            
        elif trigger_kind == "appointment_reminder":
            days = trigger_payload.get("days_until", 0)
            primary_signal = f"Their {service} appointment is in {days} days."
            supporting_fact = "Confirming now reduces no-shows."
            recommended_action = f"Ask exactly: 'Your {service} is in {days} days — can you confirm with a quick Yes?'"
            urgency_hook = "Confirming early helps us hold your slot."
            
        elif trigger_kind == "winback":
            days = trigger_payload.get("days_since_last_visit", 0)
            primary_signal = f"It's been {days} days since their last visit."
            supporting_fact = f"Their favorite: {service}."
            recommended_action = f"Ask exactly: 'We miss you! Would you like a special offer on {service} to come back?'"
            urgency_hook = f"It's been {days} days — a small incentive now can reactivate them."
            
        elif trigger_kind == "reorder_reminder":
            days = trigger_payload.get("last_order_days", 0)
            primary_signal = f"It's been {days} days since their last order."
            supporting_fact = f"They might be running low on {service}."
            recommended_action = f"Ask exactly: 'Running low on {service}? Should we send a refill?'"
            urgency_hook = "Reordering before running out avoids gaps in treatment."
            
        elif trigger_kind == "renewal_due":
            days = trigger_payload.get("membership_expiry_days", trigger_payload.get("days_remaining", 0))
            plan = trigger_payload.get("plan", service)
            amount = trigger_payload.get("renewal_amount", "")
            
            primary_signal = f"Their {plan} plan expires in {days} days."
            if amount:
                supporting_fact = f"Renewal amount: ₹{amount}. Letting it lapse means losing all accumulated benefits."
            else:
                supporting_fact = "Letting the plan lapse means losing accumulated benefits."
            recommended_action = f"Ask exactly: 'Your {plan} plan expires in {days} days — should we renew it now?'"
            urgency_hook = f"Only {days} days left — renewing now ensures no gap in service."
            
    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------
    else:
        primary_signal = f"There is recent activity on your profile: {views} views and {calls} calls in the last 30 days (category avg: {avg_views} views, {avg_calls} calls)."
        if active_offers:
            supporting_fact = f"Your '{active_offers[0]}' offer is active."
            recommended_action = f"Ask exactly: 'Should we boost {active_offers[0]} to capture more of this traffic?'"
        else:
            supporting_fact = f"You have 0 active offers. Competitors in {locality} are running promotions."
            recommended_action = "Ask exactly: 'Would you like to create a new offer to boost your visibility?'"
        urgency_hook = "Active profiles with offers get significantly more engagement."
            
    return Decision(primary_signal, supporting_fact, recommended_action, urgency_hook)
