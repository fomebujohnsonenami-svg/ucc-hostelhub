from django.urls import path

from apps.hostels import api as hostels
from apps.messaging import api as messaging
from apps.moderation import api as moderation
from apps.roommates import api as roommates
from apps.subscriptions import api as subscriptions
from common import workspaces
from common.image_views import avatar, hostel_image_detail, hostel_image_upload
from common.views import health

urlpatterns = [
    path("api/health/", health, name="health"),
    path("api/hostels/", hostels.PublicHostels.as_view(), name="public-hostels"),
    path("api/hostels/<uuid:pk>/", hostels.PublicHostel.as_view(), name="public-hostel"),
    path("api/hostels/<uuid:pk>/photos/<uuid:image_id>/", hostels.public_photo, name="public-hostel-photo"),
    path("api/manager/hostels/", hostels.ManagerHostels.as_view(), name="manager-hostels"),
    path("api/manager/hostels/<uuid:pk>/", hostels.ManagerHostel.as_view(), name="manager-hostel"),
    path("api/profile/avatar/", avatar, name="profile-avatar"),
    path("api/hostels/<uuid:hostel_id>/images/", hostel_image_upload, name="hostel-image-upload"),
    path("api/hostels/<uuid:hostel_id>/images/<uuid:image_id>/", hostel_image_detail, name="hostel-image-detail"),

    path("api/onboarding/", workspaces.Onboarding.as_view()),
    path("api/subscription-plans/", subscriptions.Plans.as_view()),
    path("api/manager/promotions/", subscriptions.Promotions.as_view()),
    path("api/manager/promotions/<uuid:pk>/", subscriptions.Promotion.as_view()),
    path("api/me/", workspaces.Me.as_view()),
    path("api/dashboard/student/", workspaces.StudentDashboard.as_view()),
    path("api/dashboard/manager/", workspaces.ManagerDashboard.as_view()),
    path("api/dashboard/admin/", workspaces.AdminDashboard.as_view()),
    path("api/amenities/", hostels.Amenities.as_view()),
    path("api/hostel-filters/", hostels.DiscoveryOptions.as_view()),
    path("api/saved-hostels/", hostels.SavedListings.as_view()),
    path("api/saved-hostels/ids/", hostels.SavedIds.as_view()),
    path("api/saved-hostels/<uuid:pk>/", hostels.SavedListing.as_view()),
    path("api/manager/hostels/<uuid:pk>/publication/", hostels.Publication.as_view()),
    path("api/manager/hostels/<uuid:hostel_id>/rooms/", hostels.ManagerRooms.as_view()),
    path("api/manager/hostels/<uuid:hostel_id>/rooms/<uuid:pk>/", hostels.ManagerRoom.as_view()),
    path("api/roommates/", roommates.Roommates.as_view()),
    path("api/roommates/me/", roommates.OwnRoommate.as_view()),
    path("api/roommates/<uuid:pk>/", roommates.RoommateDetail.as_view()),
    path("api/conversations/", messaging.Conversations.as_view()),
    path("api/conversations/<uuid:pk>/", messaging.ConversationDetail.as_view()),
    path("api/conversations/<uuid:pk>/messages/", messaging.Messages.as_view()),
    path("api/conversations/<uuid:pk>/read/", messaging.ReadMessages.as_view()),
    path("api/reports/", moderation.ReportContent.as_view()),
    path("api/admin/users/", moderation.Users.as_view()),
    path("api/admin/listings/", moderation.Listings.as_view()),
    path("api/admin/listings/<uuid:pk>/", moderation.ListingAction.as_view()),
    path("api/admin/managers/", moderation.Managers.as_view()),
    path("api/admin/managers/<uuid:pk>/", moderation.VerifyManager.as_view()),
    path("api/admin/reports/", moderation.Reports.as_view()),
    path("api/admin/reports/<uuid:pk>/", moderation.ReportAction.as_view()),
]
