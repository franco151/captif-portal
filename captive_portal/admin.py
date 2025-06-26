from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Avg
from .models import UserSession, NetworkActivity, DeviceFingerprint, BandwidthUsage

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'mac_address', 'ip_address', 'start_time', 'duration', 'data_usage', 'is_active']
    list_filter = ['is_active', 'start_time', 'user__subscription__plan']
    search_fields = ['user__username', 'mac_address', 'ip_address', 'user__phone_number']
    readonly_fields = ['start_time', 'total_activities', 'total_data_transfer']
    date_hierarchy = 'start_time'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('activities')
    
    def duration(self, obj):
        if obj.end_time:
            duration = obj.end_time - obj.start_time
            return f"{duration.total_seconds() // 3600:.0f}h {(duration.total_seconds() % 3600) // 60:.0f}m"
        return "En cours"
    duration.short_description = 'Durée'
    
    def data_usage(self, obj):
        total = obj.activities.aggregate(
            total_up=Sum('bytes_uploaded'),
            total_down=Sum('bytes_downloaded')
        )
        if total['total_up'] or total['total_down']:
            total_mb = ((total['total_up'] or 0) + (total['total_down'] or 0)) / (1024 * 1024)
            return f"{total_mb:.2f} MB"
        return "0 MB"
    data_usage.short_description = 'Données utilisées'
    
    def total_activities(self, obj):
        return obj.activities.count()
    total_activities.short_description = 'Nombre d\'activités'
    
    def total_data_transfer(self, obj):
        return self.data_usage(obj)
    total_data_transfer.short_description = 'Transfert total'

@admin.register(NetworkActivity)
class NetworkActivityAdmin(admin.ModelAdmin):
    list_display = ['session_user', 'activity_type', 'timestamp', 'ip_address', 'data_transfer_display', 'bandwidth_usage']
    list_filter = ['activity_type', 'timestamp', 'session__user__subscription__plan']
    search_fields = ['session__user__username', 'ip_address', 'mac_address']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp', 'total_data_transfer']
    
    def session_user(self, obj):
        return obj.session.user.username
    session_user.short_description = 'Utilisateur'
    
    def data_transfer_display(self, obj):
        if obj.total_data_transfer > 0:
            mb = obj.data_transfer_mb
            if mb > 1024:
                return f"{mb/1024:.2f} GB"
            return f"{mb:.2f} MB"
        return "0 MB"
    data_transfer_display.short_description = 'Transfert de données'

@admin.register(DeviceFingerprint)
class DeviceFingerprintAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'device_type', 'operating_system', 'browser', 'is_trusted', 'last_seen']
    list_filter = ['device_type', 'operating_system', 'is_trusted', 'last_seen']
    search_fields = ['user__username', 'mac_address', 'device_name']
    readonly_fields = ['first_seen', 'last_seen']
    
    actions = ['mark_as_trusted', 'mark_as_untrusted']
    
    def mark_as_trusted(self, request, queryset):
        queryset.update(is_trusted=True)
    mark_as_trusted.short_description = "Marquer comme appareil de confiance"
    
    def mark_as_untrusted(self, request, queryset):
        queryset.update(is_trusted=False)
    mark_as_untrusted.short_description = "Marquer comme appareil non fiable"

@admin.register(BandwidthUsage)
class BandwidthUsageAdmin(admin.ModelAdmin):
    list_display = ['session_user', 'timestamp', 'download_speed', 'upload_speed', 'ping_latency', 'total_data']
    list_filter = ['timestamp']
    search_fields = ['session__user__username']
    date_hierarchy = 'timestamp'
    
    def session_user(self, obj):
        return obj.session.user.username
    session_user.short_description = 'Utilisateur'
    
    def total_data(self, obj):
        total_mb = (obj.total_uploaded + obj.total_downloaded) / (1024 * 1024)
        return f"{total_mb:.2f} MB"
    total_data.short_description = 'Données totales'