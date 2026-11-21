# Premium plans and presentation mode

The public **Pricing** page reads its catalogue from Django. Student Premium is **GH₵20 per month** for in-app messaging. Hostel Manager Premium is **GH₵50 per month** for listing promotion and inquiry analytics. Discovery, saved hostels, roommate browsing and profile editing stay available to students. Managers can manage their properties and reply to inquiries without a subscription.

## Run the university presentation

1. Apply the Django migrations with `python manage.py migrate --noinput` in `backend/`. This adds the featured-listing field and seeds the two pricing catalogue rows.
2. Set `PRESENTATION_MODE=true` in the backend environment and `VITE_PRESENTATION_MODE=true` in the frontend environment. Restart Django and Vite or rebuild the production frontend.
3. Use an existing student and manager account. Open **Pricing**, then contact a hostel manager from a published listing or message a student from a public roommate profile. Sign-in returns students to the intended listing or profile.
4. In the manager workspace, open **Hostel Promotion**. Feature an owned, approved, published listing and check its inquiry conversation count. The featured listing appears on the homepage and in the promoted section of matching discovery results. Suspended listings lose their featured placement.

`GET /api/subscription-plans/` returns the public catalogue and the server access mode. A frontend configuration flag changes only presentation labels. Django independently requires valid account roles, conversation membership and listing ownership. Messaging and promotion remain open in both server modes while the launch preview runs.

The catalogue rows describe the planned offers. No per-user subscription is activated, payment details are never collected, and no checkout route is provided. A future rollout can enforce entitlements after it has a real subscription activation flow.
