# USER_FLOWS.md

# Book My Venue — User Flows

## 1. Customer Registration Flow

```text
1. Customer opens platform.
2. Customer clicks Register.
3. Customer enters name, email, password, phone.
4. Auth Service validates data.
5. Auth Service creates user with CUSTOMER role.
6. Customer receives success response.
7. Customer logs in.
8. Auth Service returns JWT access and refresh tokens.
```

## 2. Vendor Registration Flow

```text
1. Vendor opens platform.
2. Vendor selects Register as Vendor.
3. Vendor enters business details.
4. Auth Service creates user with VENDOR role.
5. Vendor profile is marked as PENDING_APPROVAL.
6. Admin reviews vendor.
7. Admin approves or rejects vendor.
8. Approved vendor can create venue listings.
```

## 3. Admin Login Flow

```text
1. Admin logs in.
2. Auth Service validates credentials.
3. Auth Service returns JWT with ADMIN role.
4. Admin accesses admin dashboard.
```

## 4. Vendor Venue Creation Flow

```text
1. Vendor logs in.
2. Vendor opens dashboard.
3. Vendor clicks Add Venue.
4. Vendor enters:
   - venue name
   - category
   - description
   - location
   - capacity
   - price
   - amenities
   - policies
5. Venue Service validates request.
6. Venue Service checks vendor ownership/permission.
7. Venue is saved with PENDING_APPROVAL status.
8. Admin receives venue approval notification.
```

## 5. Venue Approval Flow

```text
1. Admin opens pending venues.
2. Admin reviews venue details.
3. Admin approves or rejects venue.
4. Venue Service updates status.
5. If approved, venue becomes visible to customers.
6. Notification Service notifies vendor.
```

## 6. Customer Venue Search Flow

```text
1. Customer opens venue listing page.
2. Customer enters filters:
   - location
   - category
   - capacity
   - date/time
   - price range
   - amenities
3. Frontend sends request to Venue Service.
4. Venue Service returns approved venues.
5. If date/time is provided, frontend can call Booking Service to check availability.
6. Customer views suitable venues.
```

## 7. Customer Venue Detail Flow

```text
1. Customer clicks venue card.
2. Frontend requests venue details from Venue Service.
3. Venue Service returns:
   - venue information
   - images
   - amenities
   - policies
   - location
   - price
4. Customer selects preferred date and time.
5. Frontend calls Booking Service to check availability.
6. Booking Service returns available/not available.
```

## 8. Booking Request Flow

```text
1. Customer selects venue, date, start time, and end time.
2. Frontend sends booking request to Booking Service.
3. Booking Service validates customer JWT.
4. Booking Service checks venue exists and is approved.
5. Booking Service checks for overlapping bookings.
6. If no conflict, booking is created with PENDING status.
7. BookingCreated event is published.
8. Notification Service notifies vendor.
9. Customer sees booking request submitted.
```

## 9. Booking Conflict Flow

```text
1. Customer tries to book a venue.
2. Booking Service checks existing bookings.
3. If existing booking overlaps with requested time, request is rejected.
4. Customer receives message: selected slot is unavailable.
5. Customer may choose another slot.
```

Conflict condition:

```text
existing_start < new_end
AND
existing_end > new_start
```

## 10. Vendor Accept Booking Flow

```text
1. Vendor opens booking requests.
2. Vendor selects a pending booking.
3. Vendor clicks Accept.
4. Booking Service validates vendor owns the venue.
5. Booking Service rechecks conflict.
6. Booking status changes to ACCEPTED.
7. BookingAccepted event is published.
8. Notification Service notifies customer.
```

## 11. Vendor Reject Booking Flow

```text
1. Vendor opens booking requests.
2. Vendor selects a pending booking.
3. Vendor clicks Reject.
4. Vendor optionally enters rejection reason.
5. Booking Service validates vendor owns the venue.
6. Booking status changes to REJECTED.
7. BookingRejected event is published.
8. Notification Service notifies customer.
```

## 12. Customer Cancel Booking Flow

```text
1. Customer opens My Bookings.
2. Customer selects booking.
3. Customer clicks Cancel.
4. Booking Service validates customer owns booking.
5. Booking Service checks cancellation rules.
6. Booking status changes to CANCELLED if allowed.
7. BookingCancelled event is published.
8. Notification Service notifies vendor.
```

## 13. AI Venue Recommendation Flow

```text
1. Customer opens AI assistant.
2. Customer asks:
   "I need a hall in Calicut for 500 people under 80000 with parking."
3. AI Service extracts filters:
   - city: Calicut
   - capacity: 500+
   - max price: 80000
   - amenity: parking
4. AI Service calls Venue Service or uses allowed search tools.
5. Venue results are ranked.
6. AI returns recommended venues.
7. Customer selects a venue.
8. Booking Service performs actual availability check.
```

Important rule:

```text
AI recommends.
Booking Service verifies.
Database confirms.
```

## 14. RAG Venue Policy Q&A Flow

```text
1. Customer opens venue detail page.
2. Customer asks:
   "Is outside catering allowed?"
3. AI Service retrieves venue policy chunks from vector DB.
4. AI Service generates answer using retrieved policy.
5. AI response includes grounded answer.
6. If policy is missing, AI says it cannot confirm.
```

## 15. AI Booking Assistant Flow

```text
1. Customer asks AI to find a venue.
2. AI extracts requirements.
3. AI searches venues.
4. AI checks availability using Booking Service.
5. AI suggests options.
6. Customer chooses one option.
7. AI creates booking draft.
8. Customer confirms.
9. Booking Service creates actual booking.
```

The AI should not silently create confirmed bookings.

## 16. Notification Flow

```text
1. Core service publishes an event.
2. Notification Service receives event.
3. Notification Service selects template.
4. Notification Service sends email/in-app notification.
5. Notification Service stores notification log.
```

## 17. Failure Flow: AI Service Down

```text
1. Customer opens normal search.
2. AI Service is unavailable.
3. Normal venue search should still work.
4. Frontend displays AI assistant unavailable message.
```

## 18. Failure Flow: Notification Service Down

```text
1. Booking is created successfully.
2. Notification Service fails.
3. Booking should not be rolled back.
4. Event remains pending/retried.
5. Notification is sent later.
```
