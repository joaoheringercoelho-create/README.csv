import javafx.application.Application;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressBar;
import javafx.scene.control.ScrollPane;
import javafx.scene.effect.DropShadow;
import javafx.scene.layout.Background;
import javafx.scene.layout.BackgroundFill;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.CornerRadii;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.scene.paint.CycleMethod;
import javafx.scene.paint.LinearGradient;
import javafx.scene.paint.Stop;
import javafx.scene.shape.Circle;
import javafx.scene.shape.Rectangle;
import javafx.scene.text.Font;
import javafx.scene.text.FontWeight;
import javafx.scene.text.Text;
import javafx.scene.text.TextAlignment;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import javafx.stage.Stage;

public class HypeMapApp extends Application {

    private final String BG_COLOR = "#020617"; // bg-slate-950
    private final String PRIMARY_RED = "#e11d48"; // text-rose-600
    private final String GRADIENT_RED = "linear-gradient(to right, #1e3a8a, #e11d48)"; // from blue-900 to rose-600
    private final String LIST_BG_COLOR = "rgba(10, 10, 42, 0.85)"; // #0a0a2a with transparency

    @Override
    public void start(Stage primaryStage) {
        VBox mainContainer = new VBox();
        mainContainer.setStyle("-fx-background-color: " + BG_COLOR + ";");
        mainContainer.setAlignment(Pos.TOP_CENTER);

        mainContainer.getChildren().add(createHeader());
        mainContainer.getChildren().add(createHeroSection());
        mainContainer.getChildren().add(createMapWithOverlaySection());
        mainContainer.getChildren().add(createFeaturesSection());
        mainContainer.getChildren().add(createPricingSection());
        mainContainer.getChildren().add(createFooterSection());

        ScrollPane scrollPane = new ScrollPane(mainContainer);
        scrollPane.setFitToWidth(true);
        scrollPane.setStyle("-fx-background: " + BG_COLOR + "; -fx-border-color: " + BG_COLOR + ";");
        scrollPane.getStylesheets().add(createGlobalStyles());

        Scene scene = new Scene(scrollPane, 1200, 800);

        primaryStage.setTitle("HypeMap - Belo Horizonte");
        primaryStage.setScene(scene);
        primaryStage.show();
    }

    private HBox createHeader() {
        HBox header = new HBox();
        header.setPadding(new Insets(20, 50, 20, 50));
        header.setAlignment(Pos.CENTER);
        header.setStyle("-fx-background-color: rgba(2, 6, 23, 0.9); -fx-border-color: #1e293b; -fx-border-width: 0 0 1 0;");

        Text logo = new Text("HypeMap");
        logo.setFont(Font.font("SansSerif", FontWeight.BOLD, 28));
        logo.setFill(Color.web(PRIMARY_RED));

        DropShadow glow = new DropShadow();
        glow.setColor(Color.web(PRIMARY_RED));
        glow.setRadius(10);
        logo.setEffect(glow);

        Region spacer1 = new Region();
        HBox.setHgrow(spacer1, Priority.ALWAYS);

        HBox navLinks = new HBox(30);
        navLinks.setAlignment(Pos.CENTER);
        String navStyle = "-fx-text-fill: #cbd5e1; -fx-font-family: 'SansSerif'; -fx-font-size: 16px; -fx-background-color: transparent; -fx-cursor: hand;";

        Button mapLink = new Button("Mapa"); mapLink.setStyle(navStyle);
        Button featuresLink = new Button("Destaques"); featuresLink.setStyle(navStyle);
        Button plansLink = new Button("Planos"); plansLink.setStyle(navStyle);

        navLinks.getChildren().addAll(mapLink, featuresLink, plansLink);

        Region spacer2 = new Region();
        HBox.setHgrow(spacer2, Priority.ALWAYS);

        Button downloadBtn = new Button("Baixar App");
        downloadBtn.setStyle("-fx-background-color: " + PRIMARY_RED + "; -fx-text-fill: white; -fx-font-weight: bold; -fx-background-radius: 20; -fx-padding: 10 25; -fx-cursor: hand;");

        header.getChildren().addAll(logo, spacer1, navLinks, spacer2, downloadBtn);
        return header;
    }

    private VBox createHeroSection() {
        VBox hero = new VBox(20);
        hero.setPadding(new Insets(80, 50, 80, 50));
        hero.setAlignment(Pos.CENTER);

        Text title = new Text("Descubra a cidade em tempo real.");
        title.setFont(Font.font("SansSerif", FontWeight.BOLD, 56));
        title.setFill(Color.WHITE);
        title.setTextAlignment(TextAlignment.CENTER);

        Text subtitle = new Text("Veja a movimentação, os melhores eventos e escolha o rolê perfeito sem perder tempo. HypeMap conecta você aos locais mais badalados de BH.");
        subtitle.setFont(Font.font("SansSerif", 20));
        subtitle.setFill(Color.web("#94a3b8")); // text-slate-400
        subtitle.setWrappingWidth(800);
        subtitle.setTextAlignment(TextAlignment.CENTER);

        Button ctaBtn = new Button("Explorar o Mapa");
        ctaBtn.setStyle("-fx-background-color: " + GRADIENT_RED + "; -fx-text-fill: white; -fx-font-size: 18px; -fx-font-weight: bold; -fx-background-radius: 30; -fx-padding: 15 40; -fx-cursor: hand;");

        DropShadow btnGlow = new DropShadow();
        btnGlow.setColor(Color.web(PRIMARY_RED));
        btnGlow.setRadius(15);
        ctaBtn.setEffect(btnGlow);

        hero.getChildren().addAll(title, subtitle, ctaBtn);
        return hero;
    }

    private StackPane createMapWithOverlaySection() {
        StackPane container = new StackPane();
        container.setPadding(new Insets(0, 50, 50, 50));

        // 1. MAPA (Fundo)
        StackPane mapContainer = new StackPane();
        mapContainer.setPrefHeight(600);

        WebView webView = new WebView();
        WebEngine webEngine = webView.getEngine();

        String mapHtml = "<!DOCTYPE html>\n" +
                "<html>\n" +
                "<head>\n" +
                "    <title>HypeMap BH</title>\n" +
                "    <meta charset=\"utf-8\" />\n" +
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n" +
                "    <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" />\n" +
                "    <script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>\n" +
                "    <style>\n" +
                "        body { padding: 0; margin: 0; background-color: #020617; }\n" +
                "        #map { height: 100vh; width: 100vw; background-color: #020617; }\n" +
                "        .leaflet-container { background: #020617; }\n" +
                "         /* \n" +
                "             */ \n" +
                "        }\n" +
                "        .pulse { display: block; border-radius: 50%; background: #e11d48; cursor: pointer; box-shadow: 0 0 15px #e11d48; animation: pulse-animation 2s infinite; }\n" +
                "        .pulse-yellow { background: #eab308; box-shadow: 0 0 15px #eab308; }\n" +
                "        .pulse-green { background: #22c55e; box-shadow: 0 0 15px #22c55e; }\n" +
                "        @keyframes pulse-animation {\n" +
                "            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(225, 29, 72, 0.7); }\n" +
                "            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(225, 29, 72, 0); }\n" +
                "            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(225, 29, 72, 0); }\n" +
                "        }\n" +
                "    </style>\n" +
                "</head>\n" +
                "<body>\n" +
                "<div id=\"map\"></div>\n" +
                "<script>\n" +
                "    var map = L.map('map', { zoomControl: false }).setView([-19.9167, -43.9345], 13); // BH Coordinates\n" +
                "    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {\n" +
                "        attribution: '&copy; OpenStreetMap contributors',\n" +
                "        subdomains: 'abcd',\n" +
                "        maxZoom: 20\n" +
                "    }).addTo(map);\n" +
                "\n" +
                "    function createPulseIcon(colorClass) {\n" +
                "        return L.divIcon({\n" +
                "            className: 'pulse ' + colorClass,\n" +
                "            iconSize: [20, 20]\n" +
                "        });\n" +
                "    }\n" +
                "\n" +
                "    L.marker([-19.8967, -43.9245], {icon: createPulseIcon('')}).addTo(map).bindPopup('<b>Rua Alberto Cintra</b><br>Muito Movimentado (95%)');\n" +
                "    L.marker([-19.9212, -43.9405], {icon: createPulseIcon('')}).addTo(map).bindPopup('<b>Mercado Novo</b><br>Movimentado (90%)');\n" +
                "    L.marker([-19.8658, -43.9678], {icon: createPulseIcon('pulse-yellow')}).addTo(map).bindPopup('<b>Mineirão</b><br>Moderado (84%)');\n" +
                "    L.marker([-19.9165, -43.9348], {icon: createPulseIcon('pulse-green')}).addTo(map).bindPopup('<b>Sapucaí</b><br>Tranquilo (68%)');\n" +
                "</script>\n" +
                "</body>\n" +
                "</html>";

        webEngine.loadContent(mapHtml);

        Rectangle clip = new Rectangle(1100, 600);
        clip.setArcWidth(30);
        clip.setArcHeight(30);
        webView.setClip(clip);

        StackPane innerMapWrap = new StackPane(webView);
        innerMapWrap.setMaxSize(1100, 600);
        innerMapWrap.setStyle("-fx-background-color: transparent; -fx-border-color: #1e3a8a; -fx-border-width: 2; -fx-border-radius: 15; -fx-background-radius: 15;");

        mapContainer.getChildren().add(innerMapWrap);

        // 2. LISTA (Overlay Flutuante)
        VBox overlayListPanel = createOverlayListPanel();

        // Alinhamento da lista no canto esquerdo ou centro superior
        StackPane.setAlignment(overlayListPanel, Pos.CENTER_LEFT);
        StackPane.setMargin(overlayListPanel, new Insets(40, 0, 40, 40));

        container.getChildren().addAll(mapContainer, overlayListPanel);

        return container;
    }

    private VBox createOverlayListPanel() {
        VBox panel = new VBox(15);
        panel.setMaxSize(480, 520);
        panel.setPadding(new Insets(20));
        panel.setStyle("-fx-background-color: " + LIST_BG_COLOR + "; -fx-background-radius: 20;");

        DropShadow neonBorder = new DropShadow();
        neonBorder.setColor(Color.web("#e11d48"));
        neonBorder.setRadius(15);
        neonBorder.setSpread(0.2);
        panel.setEffect(neonBorder);

        // Title
        Text listTitle = new Text("Locais mais badalados");
        listTitle.setFont(Font.font("SansSerif", FontWeight.BOLD, 22));
        listTitle.setFill(Color.WHITE);

        // Tabs Header
        HBox tabsBox = new HBox(10);
        tabsBox.setAlignment(Pos.CENTER_LEFT);

        Button tabAll = createTab("Todos", true, "#ff3333", "#ff9933", null);
        Button tabBars = createTab("Bares", false, null, null, "#00ffff");
        Button tabRestaurants = createTab("Restaurantes", false, null, null, "#ff00ff");
        Button tabShows = createTab("Shows", false, null, null, "#ffff00");

        tabsBox.getChildren().addAll(tabAll, tabBars, tabRestaurants, tabShows);

        // List Body
        VBox listBody = new VBox(15);
        listBody.getChildren().addAll(
            createListItem("1", "Rua Alberto Cintra", "Bar", "🍸🍺", "95%", "#ff0000", "#ff9900"),
            createListItem("2", "Mercado Novo", "Bar", "🏢🍻", "90%", "#0000ff", "#ff00ff"),
            createListItem("3", "Mineirão", "Show", "🎤🏟️", "84%", "#ff9900", "#ffd700"),
            createListItem("4", "Sapucaí", "Bar", "🎭🍾", "68%", "#adff2f", "#90ee90")
        );

        ScrollPane listScroll = new ScrollPane(listBody);
        listScroll.setFitToWidth(true);
        listScroll.setStyle("-fx-background: transparent; -fx-background-color: transparent;");
        listScroll.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        listScroll.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);

        panel.getChildren().addAll(listTitle, tabsBox, listScroll);
        return panel;
    }

    private Button createTab(String text, boolean active, String gradStart, String gradEnd, String neonBorderColor) {
        Button btn = new Button(text);
        btn.setFont(Font.font("SansSerif", active ? FontWeight.BOLD : FontWeight.NORMAL, 14));
        btn.setTextFill(active ? Color.WHITE : Color.web("#cbd5e1"));

        if (active) {
            btn.setStyle("-fx-background-color: linear-gradient(to right, " + gradStart + ", " + gradEnd + "); -fx-background-radius: 15; -fx-padding: 5 15; -fx-cursor: hand;");
            DropShadow glow = new DropShadow(); glow.setColor(Color.web(gradStart)); glow.setRadius(5); btn.setEffect(glow);
        } else {
            btn.setStyle("-fx-background-color: transparent; -fx-border-color: " + neonBorderColor + "; -fx-border-radius: 15; -fx-padding: 4 14; -fx-cursor: hand;");
            DropShadow glow = new DropShadow(); glow.setColor(Color.web(neonBorderColor)); glow.setRadius(3); glow.setSpread(0.1); btn.setEffect(glow);
        }
        return btn;
    }

    private HBox createListItem(String rank, String name, String type, String iconTxt, String pct, String ringColor, String endGradColor) {
        HBox card = new HBox(15);
        card.setPadding(new Insets(10, 15, 10, 15));
        card.setAlignment(Pos.CENTER_LEFT);
        card.setStyle("-fx-background-color: rgba(255, 255, 255, 0.05); -fx-background-radius: 10; -fx-border-color: " + ringColor + "; -fx-border-radius: 10; -fx-border-width: 1;");

        DropShadow innerGlow = new DropShadow();
        innerGlow.setColor(Color.web(ringColor));
        innerGlow.setRadius(5);
        innerGlow.setSpread(0.1);
        card.setEffect(innerGlow);

        StackPane rankPane = new StackPane();
        Circle baseCircle = new Circle(18);
        baseCircle.setFill(Color.web("#333"));
        baseCircle.setStroke(Color.web(ringColor));
        baseCircle.setStrokeWidth(2);
        Text rankText = new Text("#" + rank);
        rankText.setFill(Color.WHITE);
        rankText.setFont(Font.font("SansSerif", FontWeight.BOLD, 14));
        rankPane.getChildren().addAll(baseCircle, rankText);

        VBox infoBox = new VBox(2);
        Text nameTxt = new Text(name);
        nameTxt.setFont(Font.font("SansSerif", FontWeight.BOLD, 16));
        nameTxt.setFill(Color.WHITE);
        Text typeTxt = new Text(type);
        typeTxt.setFont(Font.font("SansSerif", 12));
        typeTxt.setFill(Color.web("#94a3b8"));
        infoBox.getChildren().addAll(nameTxt, typeTxt);

        Text icon = new Text(iconTxt);
        icon.setFont(Font.font(24));

        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);

        VBox metricBox = new VBox(5);
        metricBox.setAlignment(Pos.CENTER_RIGHT);

        HBox topMetric = new HBox(5);
        topMetric.setAlignment(Pos.CENTER_RIGHT);
        Text flame = new Text("🔥"); flame.setFont(Font.font(14));
        Text pctTxt = new Text(pct);
        pctTxt.setFill(Color.WHITE);
        pctTxt.setFont(Font.font("SansSerif", FontWeight.BOLD, 14));
        topMetric.getChildren().addAll(flame, pctTxt);

        StackPane barWrap = new StackPane();
        barWrap.setAlignment(Pos.CENTER_LEFT);
        Rectangle barBg = new Rectangle(60, 6, Color.web("#333"));
        barBg.setArcWidth(6); barBg.setArcHeight(6);

        double widthPct = Double.parseDouble(pct.replace("%","")) / 100.0 * 60.0;
        Rectangle barFill = new Rectangle(widthPct, 6);
        barFill.setArcWidth(6); barFill.setArcHeight(6);
        barFill.setFill(LinearGradient.valueOf("linear-gradient(to right, " + ringColor + ", " + endGradColor + ")"));

        barWrap.getChildren().addAll(barBg, barFill);

        metricBox.getChildren().addAll(topMetric, barWrap);

        card.getChildren().addAll(rankPane, infoBox, spacer, icon, metricBox);
        return card;
    }

    private VBox createFeaturesSection() {
        VBox section = new VBox(40);
        section.setPadding(new Insets(60, 50, 60, 50));
        section.setAlignment(Pos.CENTER);

        Text title = new Text("Por que usar o HypeMap?");
        title.setFont(Font.font("SansSerif", FontWeight.BOLD, 36));
        title.setFill(Color.WHITE);

        HBox grid = new HBox(30);
        grid.setAlignment(Pos.CENTER);

        grid.getChildren().addAll(
            createFeatureCard("🗺️", "Movimento em Tempo Real", "Veja no mapa quais os locais mais quentes e evite filas ou lugares vazios demais."),
            createFeatureCard("📅", "Eventos e Atrações", "Tenha a agenda unificada da cidade. Shows, festas, e eventos tudo num só lugar."),
            createFeatureCard("🎯", "Indicações Personalizadas", "Receba sugestões exclusivas baseadas no seu perfil e nas suas idas anteriores.")
        );

        section.getChildren().addAll(title, grid);
        return section;
    }

    private VBox createFeatureCard(String iconTxt, String title, String desc) {
        VBox card = new VBox(15);
        card.setPadding(new Insets(30));
        card.setAlignment(Pos.CENTER);
        card.setPrefWidth(300);
        card.setStyle("-fx-background-color: #0f172a; -fx-border-color: #1e293b; -fx-border-width: 1; -fx-border-radius: 15; -fx-background-radius: 15;");

        Text icon = new Text(iconTxt);
        icon.setFont(Font.font(40));

        Text titleTxt = new Text(title);
        titleTxt.setFont(Font.font("SansSerif", FontWeight.BOLD, 20));
        titleTxt.setFill(Color.WHITE);
        titleTxt.setTextAlignment(TextAlignment.CENTER);

        Text descTxt = new Text(desc);
        descTxt.setFont(Font.font("SansSerif", 14));
        descTxt.setFill(Color.web("#94a3b8"));
        descTxt.setTextAlignment(TextAlignment.CENTER);
        descTxt.setWrappingWidth(260);

        card.getChildren().addAll(icon, titleTxt, descTxt);
        return card;
    }

    private VBox createPricingSection() {
        VBox section = new VBox(40);
        section.setPadding(new Insets(60, 50, 80, 50));
        section.setAlignment(Pos.CENTER);

        Text title = new Text("Escolha seu Plano");
        title.setFont(Font.font("SansSerif", FontWeight.BOLD, 36));
        title.setFill(Color.WHITE);

        HBox grid = new HBox(30);
        grid.setAlignment(Pos.CENTER);

        grid.getChildren().addAll(
            createPriceCard("Básico", "R$ 2,00", "/mês", "Acesso aos mapas e estabelecimentos.", false),
            createPriceCard("Hype", "R$ 5,00", "/mês", "Acesso ao nível de movimentação em tempo real e filtros.", true),
            createPriceCard("VIP", "R$ 10,00", "/mês", "Acesso total, eventos exclusivos, promoções e sem anúncios.", false)
        );

        section.getChildren().addAll(title, grid);
        return section;
    }

    private VBox createPriceCard(String name, String price, String freq, String desc, boolean isHighlighted) {
        VBox card = new VBox(20);
        card.setPadding(new Insets(40, 30, 40, 30));
        card.setAlignment(Pos.CENTER);
        card.setPrefWidth(300);

        if (isHighlighted) {
            card.setStyle("-fx-background-color: #0f172a; -fx-border-color: " + PRIMARY_RED + "; -fx-border-width: 2; -fx-border-radius: 15; -fx-background-radius: 15;");
            DropShadow glow = new DropShadow(); glow.setColor(Color.web(PRIMARY_RED)); glow.setRadius(20); glow.setSpread(0.1);
            card.setEffect(glow);
        } else {
            card.setStyle("-fx-background-color: #0f172a; -fx-border-color: #1e293b; -fx-border-width: 1; -fx-border-radius: 15; -fx-background-radius: 15;");
        }

        Text nameTxt = new Text(name);
        nameTxt.setFont(Font.font("SansSerif", FontWeight.BOLD, 24));
        nameTxt.setFill(Color.WHITE);

        HBox priceBox = new HBox(5);
        priceBox.setAlignment(Pos.BOTTOM_CENTER);
        Text priceTxt = new Text(price);
        priceTxt.setFont(Font.font("SansSerif", FontWeight.BOLD, 36));
        priceTxt.setFill(isHighlighted ? Color.web(PRIMARY_RED) : Color.WHITE);
        Text freqTxt = new Text(freq);
        freqTxt.setFont(Font.font("SansSerif", 16));
        freqTxt.setFill(Color.web("#94a3b8"));
        priceBox.getChildren().addAll(priceTxt, freqTxt);

        Text descTxt = new Text(desc);
        descTxt.setFont(Font.font("SansSerif", 14));
        descTxt.setFill(Color.web("#94a3b8"));
        descTxt.setTextAlignment(TextAlignment.CENTER);
        descTxt.setWrappingWidth(240);

        Region spacer = new Region();
        VBox.setVgrow(spacer, Priority.ALWAYS);

        Button btn = new Button("Assinar " + name);
        if (isHighlighted) {
            btn.setStyle("-fx-background-color: " + PRIMARY_RED + "; -fx-text-fill: white; -fx-font-weight: bold; -fx-background-radius: 20; -fx-padding: 10 30; -fx-cursor: hand;");
        } else {
            btn.setStyle("-fx-background-color: #1e293b; -fx-text-fill: white; -fx-font-weight: bold; -fx-background-radius: 20; -fx-padding: 10 30; -fx-cursor: hand;");
        }

        card.getChildren().addAll(nameTxt, priceBox, descTxt, spacer, btn);
        return card;
    }

    private VBox createFooterSection() {
        VBox footer = new VBox(10);
        footer.setPadding(new Insets(40, 50, 40, 50));
        footer.setAlignment(Pos.CENTER);
        footer.setStyle("-fx-background-color: #020617; -fx-border-color: #1e293b; -fx-border-width: 1 0 0 0;");

        Text links = new Text("Termos de Uso | Privacidade | Contato");
        links.setFont(Font.font("SansSerif", 14));
        links.setFill(Color.web("#94a3b8"));

        Text copyright = new Text("© 2024 HypeMap. Todos os direitos reservados.");
        copyright.setFont(Font.font("SansSerif", 12));
        copyright.setFill(Color.web("#64748b"));

        footer.getChildren().addAll(links, copyright);
        return footer;
    }

    private String createGlobalStyles() {
        return "data:text/css," +
                ".scroll-bar:vertical {" +
                "    -fx-background-color: transparent;" +
                "    -fx-pref-width: 12px;" +
                "}" +
                ".scroll-bar:vertical .track {" +
                "    -fx-background-color: #020617;" +
                "    -fx-border-color: transparent;" +
                "    -fx-border-radius: 5px;" +
                "}" +
                ".scroll-bar:vertical .thumb {" +
                "    -fx-background-color: linear-gradient(to right, #444, #888, #444);" +
                "    -fx-background-radius: 5px;" +
                "    -fx-border-color: #00FFFF;" +
                "    -fx-border-radius: 5px;" +
                "}" +
                ".scroll-pane > .viewport {" +
                "    -fx-background-color: transparent;" +
                "}";
    }

    public static void main(String[] args) {
        launch(args);
    }
}
