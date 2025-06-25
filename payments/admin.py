from django.contrib import admin
from django.urls import path
from . import views
from .models import Payment
from django.db import connection
from django.db import models
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.utils import timezone
from django.urls import reverse

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'user', 'plan', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('receipt_number', 'user__username', 'user__email')
    ordering = ('-created_at',)
    actions = ['export_as_pdf']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('print/<int:payment_id>/', self.admin_site.admin_view(views.print_receipt), name='print-payment-receipt'),
        ]
        return custom_urls + urls

    # Dans la méthode changelist_view, ajoutez les données pour les graphiques
    def changelist_view(self, request, extra_context=None):
        # Récupérer les statistiques avec des requêtes SQL directes
        with connection.cursor() as cursor:
            # Nombre total de paiements
            cursor.execute("SELECT COUNT(*) FROM payments_payment")
            total_payments = cursor.fetchone()[0]

            # Montant total des paiements réussis
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM payments_payment 
                WHERE status = 'SUCCESS'
            """)
            total_amount = cursor.fetchone()[0]

        # Récupérer les statistiques complètes
        stats = Payment.get_statistics()
        
        # Préparer les données pour les graphiques
        import json
        chart_labels = json.dumps([stat['day'].strftime('%d/%m/%Y') for stat in stats['daily_stats']])
        chart_data = json.dumps([float(stat['total_amount']) for stat in stats['daily_stats']])
        chart_counts = json.dumps([stat['count'] for stat in stats['daily_stats']])
        
        # Ajouter au contexte
        extra_context = extra_context or {}
        extra_context['total_payments'] = total_payments
        extra_context['total_amount'] = total_amount
        extra_context['chart_labels'] = chart_labels
        extra_context['chart_data'] = chart_data
        extra_context['chart_counts'] = chart_counts
        extra_context['statistics'] = stats
        
        # Ajouter l'URL correcte au contexte
        extra_context = extra_context or {}
        extra_context['daily_receipts_url'] = '/api/daily-receipts-redirect/'
        
        return super().changelist_view(request, extra_context=extra_context)

    def print_receipt(self, request, payment_id):
        payment = Payment.objects.get(id=payment_id)
        return payment.generate_receipt_pdf()

    def export_as_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="payment_statistics.pdf"'
        
        # Créer le document PDF
        doc = SimpleDocTemplate(response, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Style personnalisé pour les titres
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        
        # En-tête
        elements.append(Paragraph("Statistiques des Paiements", title_style))
        elements.append(Spacer(1, 20))
        
        # Statistiques globales
        stats = Payment.get_statistics()
        
        # Tableau des statistiques globales
        global_data = [
            ['Statistique', 'Valeur'],
            ['Nombre total de paiements', f"{stats['total_payments']:,}"],
            ['Montant total', f"{stats['total_amount']:,} Ar"],
            ['Nombre d\'abonnements', f"{stats['total_subscriptions']:,}"],
            ['Montant des abonnements', f"{stats['total_subscription_amount']:,} Ar"]
        ]
        
        global_table = Table(global_data, colWidths=[3*inch, 2*inch])
        global_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(global_table)
        elements.append(Spacer(1, 30))
        
        # Tableau des forfaits
        plan_data = [['Forfait', 'Prix', 'Effectif', 'Montant Total']]
        for stat in stats['subscription_stats']:
            plan_data.append([
                stat['name'],
                f"{stat['price']:,} Ar",
                f"{stat['count']:,}",
                f"{stat['total_amount']:,} Ar"
            ])
        
        plan_table = Table(plan_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(Paragraph("Statistiques par Forfait", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(plan_table)
        elements.append(Spacer(1, 30))
        
        # Tableau des statistiques journalières
        daily_data = [['Date', 'Nombre de Paiements', 'Montant Total']]
        for stat in stats['daily_stats']:
            daily_data.append([
                stat['day'].strftime('%d/%m/%Y'),
                f"{stat['count']:,}",
                f"{stat['total_amount']:,} Ar"
            ])
        
        daily_table = Table(daily_data, colWidths=[2*inch, 2*inch, 2*inch])
        daily_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(Paragraph("Statistiques Journalières", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(daily_table)
        
        # Ajoutez ces imports
        import matplotlib.pyplot as plt
        import io
        from reportlab.lib.utils import ImageReader
        
        # Dans la méthode export_as_pdf, ajoutez après les tableaux
        # Créer un graphique avec matplotlib
        buffer = io.BytesIO()
        plt.figure(figsize=(8, 4))
        
        # Données pour le graphique
        dates = [stat['day'].strftime('%d/%m/%Y') for stat in stats['daily_stats']]
        amounts = [float(stat['total_amount']) for stat in stats['daily_stats']]
        
        # Créer le graphique à barres
        plt.bar(dates, amounts, color='skyblue')
        plt.title('Montant total par jour')
        plt.xlabel('Date')
        plt.ylabel('Montant (Ar)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Sauvegarder le graphique dans le buffer
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()
        
        # Ajouter le graphique au PDF
        elements.append(Paragraph("Graphique des montants journaliers", styles['Heading2']))
        elements.append(Spacer(1, 10))
        elements.append(Image(ImageReader(buffer), width=6*inch, height=3*inch))
        elements.append(Spacer(1, 20))
        
        # Pied de page
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            spaceBefore=20
        )
        elements.append(Paragraph(f"Rapport généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
        elements.append(Paragraph("BestConnect - Votre connexion internet de confiance", footer_style))
        elements.append(Paragraph("Contact: 0347249715", footer_style))
        
        # Générer le PDF
        doc.build(elements)
        return response
    export_as_pdf.short_description = "Exporter les statistiques en PDF"