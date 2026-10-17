import Foundation
import Postbox
import TelegramApi
import SwiftSignalKit

public struct ModStoredNFTGift: Codable, Equatable {
    public var id: Int64
    public var title: String
    public var number: Int32
    public var modelName: String
    public var backdropId: Int32
    public var innerColor: Int32
    public var outerColor: Int32
    public var patternColor: Int32
    public var textColor: Int32
    public var date: Int32
    
    public init(
        id: Int64,
        title: String,
        number: Int32,
        modelName: String,
        backdropId: Int32,
        innerColor: Int32,
        outerColor: Int32,
        patternColor: Int32,
        textColor: Int32,
        date: Int32
    ) {
        self.id = id
        self.title = title
        self.number = number
        self.modelName = modelName
        self.backdropId = backdropId
        self.innerColor = innerColor
        self.outerColor = outerColor
        self.patternColor = patternColor
        self.textColor = textColor
        self.date = date
    }
}

public final class ModNFTGiftsManager {
    public static let shared = ModNFTGiftsManager()
    
    private let storageKey = "mod_nft_gifts_items"
    
    public var customGiftsCount: Int {
        return self.getStoredGifts().count
    }
    
    public init() {}
    
    public func getStoredGifts() -> [ModStoredNFTGift] {
        guard let data = UserDefaults.standard.data(forKey: self.storageKey) else {
            return []
        }
        do {
            return try JSONDecoder().decode([ModStoredNFTGift].self, from: data)
        } catch {
            return []
        }
    }
    
    public func saveStoredGifts(_ gifts: [ModStoredNFTGift]) {
        if let data = try? JSONEncoder().encode(gifts) {
            UserDefaults.standard.set(data, forKey: self.storageKey)
        }
    }
    
    public func addGift(
        title: String,
        number: Int32,
        modelName: String,
        backdropId: Int32 = 1,
        innerColor: Int32 = 0x2A1B4E,
        outerColor: Int32 = 0x110B29,
        patternColor: Int32 = 0x9B51E0,
        textColor: Int32 = 0xFFFFFF
    ) {
        var gifts = self.getStoredGifts()
        let newId = Int64(arc4random()) | (Int64(arc4random()) << 32)
        let newGift = ModStoredNFTGift(
            id: abs(newId),
            title: title,
            number: number,
            modelName: modelName,
            backdropId: backdropId,
            innerColor: innerColor,
            outerColor: outerColor,
            patternColor: patternColor,
            textColor: textColor,
            date: Int32(Date().timeIntervalSince1970)
        )
        gifts.insert(newGift, at: 0)
        self.saveStoredGifts(gifts)
    }
    
    public func clearGifts() {
        UserDefaults.standard.removeObject(forKey: self.storageKey)
    }
    
    public func getCustomGifts(accountPeerId: EnginePeer.Id = EnginePeer.Id(0)) -> [ProfileGiftsContext.State.StarGift] {
        return self.injectCustomGifts(into: [], accountPeerId: accountPeerId)
    }
    
    public func injectCustomGifts(
        into existing: [ProfileGiftsContext.State.StarGift],
        accountPeerId: EnginePeer.Id
    ) -> [ProfileGiftsContext.State.StarGift] {
        let stored = self.getStoredGifts()
        if stored.isEmpty {
            return existing
        }
        
        var generated: [ProfileGiftsContext.State.StarGift] = []
        for item in stored {
            let resource = CloudDocumentMediaResource(
                datacenterId: 1,
                fileId: item.id,
                accessHash: 0,
                size: 1024,
                fileReference: Data(),
                fileName: "\(item.modelName).tgs"
            )
            let dummyFile = TelegramMediaFile(
                fileId: MediaId(namespace: Namespaces.Media.CloudFile, id: item.id),
                partialReference: nil,
                resource: resource,
                previewRepresentations: [],
                videoThumbnails: [],
                videoCover: nil,
                immediateThumbnailData: nil,
                mimeType: "application/x-tgsticker",
                size: 1024,
                attributes: [.FileName(fileName: "\(item.modelName).tgs")],
                alternativeRepresentations: []
            )
            
            let uniqueGift = StarGift.UniqueGift(
                id: item.id,
                giftId: item.id,
                title: item.title,
                number: item.number,
                slug: "\(item.title.replacingOccurrences(of: " ", with: ""))-\(item.number)",
                owner: .peerId(accountPeerId),
                attributes: [
                    .model(name: item.modelName, file: dummyFile, rarity: .legendary, crafted: false),
                    .backdrop(
                        name: "CustomBackdrop",
                        id: item.backdropId,
                        innerColor: item.innerColor,
                        outerColor: item.outerColor,
                        patternColor: item.patternColor,
                        textColor: item.textColor,
                        rarity: .rare
                    ),
                    .originalInfo(
                        senderPeerId: nil,
                        recipientPeerId: accountPeerId,
                        date: item.date,
                        text: "Custom Unique NFT Gift",
                        entities: nil
                    )
                ],
                availability: StarGift.UniqueGift.Availability(issued: 1, total: 1),
                giftAddress: nil,
                resellAmounts: [],
                resellForTonOnly: false,
                releasedBy: accountPeerId,
                valueAmount: nil,
                valueCurrency: nil,
                valueUsdAmount: nil,
                flags: [.isThemeAvailable],
                themePeerId: nil,
                peerColor: nil,
                hostPeerId: nil,
                minOfferStars: nil,
                craftChancePermille: nil
            )
            
            let profileGift = ProfileGiftsContext.State.StarGift(
                gift: .unique(uniqueGift),
                reference: nil,
                fromPeer: nil,
                date: item.date,
                text: "Created with StarGift Constructor",
                entities: nil,
                nameHidden: false,
                savedToProfile: true,
                pinnedToTop: false,
                convertStars: nil,
                canUpgrade: false,
                canExportDate: nil,
                upgradeStars: nil,
                transferStars: nil,
                canTransferDate: nil,
                canResaleDate: nil,
                collectionIds: nil,
                prepaidUpgradeHash: nil,
                upgradeSeparate: false,
                dropOriginalDetailsStars: nil,
                number: item.number,
                isRefunded: false,
                canCraftAt: nil
            )
            generated.append(profileGift)
        }
        
        return generated + existing
    }
}
